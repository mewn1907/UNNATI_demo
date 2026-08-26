"""WhatsApp-style conversational experience (demo simulator).

Farmers talk naturally; the bot extracts crop / quantity / location / harvest,
asks for missing pieces one at a time, runs the SAME deterministic
recommendation engine as the web app, and lets the farmer join the load.

Extraction order: LLM (if enabled) → deterministic Hinglish rules fallback.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.mandi import Mandi
from app.models.recommendation import Recommendation
from app.schemas.chat import ChatMessageOut, QuickReply
from app.schemas.recommendation import RecommendationResponse
from app.services import llm_service
from app.services.recommendation_service import NoValidMatchError, get_recommendation, join_pool

logger = logging.getLogger("Unnati.chat")

CHAT_FARMER_NAME = "WhatsApp Demo Farmer"
CHAT_FARMER_PHONE = "+91-90000-90909"

CROP_SYNONYMS = {
    "tomato": "Tomato", "tomatoes": "Tomato", "tamatar": "Tomato", "tmatar": "Tomato",
    "potato": "Potato", "potatoes": "Potato", "aloo": "Potato", "aalu": "Potato",
    "onion": "Onion", "onions": "Onion", "pyaz": "Onion", "pyaaj": "Onion", "piyaz": "Onion",
    "cabbage": "Cabbage", "band gobhi": "Cabbage", "patta gobhi": "Cabbage",
    "cauliflower": "Cauliflower", "phool gobhi": "Cauliflower", "gobhi": "Cauliflower",
    "mango": "Mango", "mangoes": "Mango", "aam": "Mango",
    "banana": "Banana", "bananas": "Banana", "kela": "Banana",
    "apple": "Apple", "apples": "Apple", "seb": "Apple",
    "wheat": "Wheat", "gehun": "Wheat", "kanak": "Wheat",
    "rice": "Rice", "chawal": "Rice", "dhaan": "Rice", "dhan": "Rice",
}

LOCATION_EXTRA_NAMES = {
    "delhi": ("Delhi NCR", 28.6139, 77.209),
    "ncr": ("Delhi NCR", 28.6139, 77.209),
    "delhi ncr": ("Delhi NCR", 28.6139, 77.209),
    "azadpur": ("Azadpur, Delhi", 28.7056, 77.17),
}

_QUANTITY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(quintal|quintals|kuintal|kwintal|tonne?s?|kg|kgs|kilo[s]?|kilograms?)?",
    re.IGNORECASE,
)
_TIME_WORDS_RE = re.compile(r"in\s*\d+\s*(din|days?|hours?|hrs?|ghante)", re.IGNORECASE)


@dataclass
class ChatSession:
    crop: str | None = None
    quantity_kg: float | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    harvested_at: datetime | None = None
    listing_id: int | None = None
    recommendation: dict | None = None
    joined: bool = False
    updated_at: float = field(default_factory=time.time)

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.crop:
            missing.append("crop")
        if not self.quantity_kg:
            missing.append("quantity")
        if not self.location_name:
            missing.append("location")
        if not self.harvested_at:
            missing.append("harvest")
        return missing


_SESSIONS: dict[str, ChatSession] = {}
_LOCATION_INDEX: tuple[float, dict[str, tuple[str, float, float]]] = (0.0, {})


def _get_session(session_id: str) -> ChatSession:
    session = _SESSIONS.get(session_id)
    if session is None:
        session = ChatSession()
        _SESSIONS[session_id] = session
    session.updated_at = time.time()
    return session


def _location_index(db: Session) -> dict[str, tuple[str, float, float]]:
    """name(lower) -> (display, lat, lng); cached briefly."""
    global _LOCATION_INDEX
    now_ts = time.time()
    cached_at, cached = _LOCATION_INDEX
    if cached and now_ts - cached_at < 60:
        return cached

    index: dict[str, tuple[str, float, float]] = {}
    for village, lat, lng in db.execute(
        select(Farmer.village, Farmer.latitude, Farmer.longitude).distinct()
    ).all():
        index[str(village).lower()] = (str(village), float(lat), float(lng))
    for mandi in db.execute(select(Mandi)).scalars().all():
        index[mandi.name.lower()] = (mandi.name, mandi.latitude, mandi.longitude)
        index[mandi.city.lower()] = (mandi.city, mandi.latitude, mandi.longitude)
    index.update(LOCATION_EXTRA_NAMES)
    _LOCATION_INDEX = (now_ts, index)
    return index


def _rule_extract(text: str, db: Session) -> dict:
    """Deterministic Hinglish extraction used alongside/instead of the LLM."""
    lowered = text.lower()

    crop = None
    for synonym, canonical in CROP_SYNONYMS.items():
        if re.search(rf"\b{re.escape(synonym)}\b", lowered):
            crop = canonical
            break

    # Avoid capturing quantities embedded in time phrases like "in 3 days".
    searchable = _TIME_WORDS_RE.sub(" ", lowered)
    quantity_kg = None
    for match in _QUANTITY_RE.finditer(searchable):
        value, unit = float(match.group(1)), (match.group(2) or "").lower()
        if not unit and "." not in match.group(1) and len(match.group(1)) > 5:
            continue  # likely a phone number fragment
        if unit.startswith(("quintal", "kuintal", "kwintal")):
            quantity_kg = value * 100
        elif unit.startswith("ton"):
            quantity_kg = value * 1000
        elif unit in ("kg", "kgs", "kilo", "kilos", "kilogram", "kilograms"):
            quantity_kg = value
        elif unit == "" and value >= 20:  # bare number near crop context => kg
            quantity_kg = value
        if quantity_kg:
            break

    location = None
    index = _location_index(db)
    best_len = 0
    for key, entry in index.items():
        if re.search(rf"\b{re.escape(key)}\b", lowered) and len(key) > best_len:
            location = entry
            best_len = len(key)

    harvested_at = None
    now = datetime.now()
    if re.search(r"\b(today|aaj|abhi|just now)\b", lowered):
        harvested_at = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if harvested_at > now:
            harvested_at = now - timedelta(hours=2)
    elif re.search(r"\b(yesterday|kal tha|beeta kal)\b", lowered):
        harvested_at = now - timedelta(days=1)
    elif re.search(r"\b(kal|tomorrow)\b", lowered):
        harvested_at = now + timedelta(days=1)
    else:
        relative = re.search(r"in\s+(\d+)\s*(din|day|days|hours?|hrs?|ghante)", lowered)
        if relative:
            amount = int(relative.group(1))
            unit_word = relative.group(2)
            delta_days = amount if unit_word.startswith(("din", "day")) else 0
            delta_hours = 0 if delta_days else amount
            harvested_at = now + timedelta(days=delta_days, hours=delta_hours)

    return {
        "crop": crop,
        "quantity_kg": quantity_kg,
        "location": location,
        "harvested_at": harvested_at,
    }


def _merge_extraction(session: ChatSession, llm_fields, rules: dict) -> None:
    if session.crop is None:
        candidates = [
            llm_fields.crop if llm_fields and llm_fields.crop else None,
            rules["crop"],
        ]
        for candidate in candidates:
            if candidate:
                matched = CROP_SYNONYMS.get(str(candidate).lower())
                session.crop = matched or str(candidate).strip().title()
                break
    if session.quantity_kg is None and rules["quantity_kg"]:
        session.quantity_kg = rules["quantity_kg"]
    elif (
        session.quantity_kg is None
        and llm_fields is not None
        and llm_fields.quantity_kg
    ):
        session.quantity_kg = llm_fields.quantity_kg
    if session.location_name is None and rules["location"]:
        display, lat, lng = rules["location"]
        session.location_name = display
        session.latitude, session.longitude = lat, lng
    elif session.location_name is None and llm_fields is not None and llm_fields.location_text:
        session.location_name = llm_fields.location_text  # unresolved; ask user to clarify
    if session.harvested_at is None and rules["harvested_at"]:
        session.harvested_at = rules["harvested_at"]


def bot(text: str, quick_replies: list[QuickReply] | None = None,
        recommendation_id: str | None = None, joined: bool = False) -> ChatMessageOut:
    return ChatMessageOut(
        role="bot", text=text, quick_replies=quick_replies or [],
        recommendation_id=recommendation_id, joined=joined,
    )


def _format_recommendation(rec: RecommendationResponse, session_crop: str) -> str:
    r = rec.recommended
    lines = [
        f"Got it! {'🍅' if 'tomato' in rec.crop_name.lower() else '🌾'}",
        f"{rec.quantity_kg:.0f} kg {rec.crop_name} · 📍 {r.pool.members[0].village if r.pool and r.pool.members else 'your farm'}",
        "",
        "🏆 *Best option for you:*",
        f"Sell at *{r.mandi_name}* ({r.price_per_kg:.0f}/kg)",
    ]
    if r.truck_id:
        trip_label = "🔁 RETURN TRIP" if r.is_return_trip else ""
        lines.append(f"🚚 Truck {r.truck_id} · departs {r.departure_at.strftime('%I:%M %p').lstrip('0')} {trip_label}")
    if r.pool and r.pool.farmer_count > 1:
        lines.append(f"👨‍🌾 Pool: {r.pool.farmer_count} farmers · {r.pool.total_quantity_kg:,.0f} kg loaded")
    if rec.net_gain > 0:
        lines.append("")
        lines.append(f"💰 You could earn *₹{rec.net_gain:,.0f} MORE* than your nearest mandi")
    risk = rec.spoilage.risk_level
    if risk in ("HIGH", "CRITICAL"):
        lines.append(f"⏱ Spoilage risk: *{risk}* — move within ~{rec.spoilage.hours_remaining:.0f}h")
    elif risk == "MEDIUM":
        lines.append(f"⏱ Spoilage watch: medium — ~{rec.spoilage.hours_remaining:.0f}h window")
    lines.append("")
    lines.append("_Prices are seeded demo values._")
    lines.append("Reply *1️⃣ Join this load* or *2️⃣ Other options*.")
    return "\n".join(lines)


def _format_alternatives(rec: RecommendationResponse) -> str:
    lines = ["Other options we found:", ""]
    options = [(rec.recommended.mandi_name, rec.recommended.net_profit)] + [
        (alt.mandi_name, alt.net_profit) for alt in rec.alternatives
    ]
    baseline_net = rec.baseline.net_profit
    lines.append(f"• Sell nearby ({rec.baseline.mandi_name}): ₹{baseline_net:,.0f} net")
    for name, net in options:
        lines.append(f"• {name}: ₹{net:,.0f} net")
    lines.append("")
    lines.append("Reply *1️⃣ Join the recommended load* or ask me anything else.")
    return "\n".join(lines)


def _handle_join(session: ChatSession, db: Session) -> ChatMessageOut:
    rec_data = session.recommendation
    if not rec_data or not rec_data.get("pool_id"):
        return bot("Please share your harvest details again — what did you harvest?")
    try:
        result = join_pool(db, rec_data["pool_id"], rec_data["listing_id"])
    except LookupError:
        return bot("That load just closed. Let's find another option — tell me your crop again.")
    departure = result.departure_at.strftime("%d %b · %I:%M %p").lstrip("0")
    session.joined = True
    return bot(
        "✅ *Load confirmed!*\n\n"
        f"{result.message}\n\n"
        f"🚚 Truck {result.truck_id}\n"
        f"🕒 Departure: {departure}\n"
        f"📍 Destination: {result.destination_mandi}\n\n"
        "You'll get reminders before departure.",
        quick_replies=[QuickReply(label="Start over", value="start over")],
        joined=True,
    )


def _produce_recommendation(session: ChatSession, db: Session) -> ChatMessageOut:
    try:
        listing = _create_listing_from_session(db, session)
    except ValueError as exc:
        return bot(f"I couldn't record that: {exc}. Let's try again — what did you harvest?")
    session.listing_id = listing.id

    try:
        rec = get_recommendation(db, listing.id)
    except NoValidMatchError:
        session.crop = None
        session.quantity_kg = None
        return bot(
            "😔 I couldn't find a safe load right now.\n\n"
            "We checked:\n"
            "• nearby farmers\n• available trucks\n• mandi routes\n"
            "• capacity\n• spoilage timing\n\n"
            "Try increasing pickup radius or another crop day. "
            "Or type *start over*."
        )

    session.recommendation = {
        "recommendation_id": rec.recommendation_id,
        "listing_id": listing.id,
        "pool_id": _pool_id_for(db, rec.recommendation_id),
    }
    return bot(
        _format_recommendation(rec, session.crop),
        quick_replies=[
            QuickReply(label="1 - Join load", value="1"),
            QuickReply(label="2 - Other options", value="2"),
            QuickReply(label="Start over", value="start over"),
        ],
        recommendation_id=rec.recommendation_id,
    )


def _pool_id_for(db: Session, recommendation_reference: str) -> int | None:
    row = db.execute(
        select(Recommendation).where(Recommendation.reference == recommendation_reference)
    ).scalar_one_or_none()
    return row.pool_id if row else None


def _create_listing_from_session(db: Session, session: ChatSession) -> FarmerListing:
    if session.latitude is None or session.longitude is None:
        raise ValueError("unknown location")

    crop = db.execute(
        select(Crop).where(func.lower(Crop.name) == (session.crop or "").lower())
    ).scalar_one_or_none()
    if crop is None:
        raise ValueError(f"unknown crop '{session.crop}'")

    farmer = db.execute(
        select(Farmer).where(Farmer.phone == CHAT_FARMER_PHONE)
    ).scalar_one_or_none()
    if farmer is None:
        farmer = Farmer(
            name=CHAT_FARMER_NAME,
            phone=CHAT_FARMER_PHONE,
            village=session.location_name or "Unknown",
            district="",
            state="",
            latitude=session.latitude,
            longitude=session.longitude,
        )
        db.add(farmer)
        db.flush()
    else:
        farmer.village = session.location_name or farmer.village
        farmer.latitude = session.latitude
        farmer.longitude = session.longitude
        db.flush()

    listing = FarmerListing(
        farmer_id=farmer.id,
        crop_id=crop.id,
        quantity_kg=float(session.quantity_kg),
        harvested_at=session.harvested_at or datetime.now() - timedelta(hours=2),
        available_until=datetime.now() + timedelta(days=3),
        latitude=session.latitude,
        longitude=session.longitude,
        status="AVAILABLE",
    )
    db.add(listing)
    db.commit()
    return listing


def handle_message(db: Session, session_id: str, text: str) -> ChatMessageOut:
    """Main conversational turn handler."""
    normalized = text.strip().lower()
    session = _get_session(session_id)

    if normalized in ("reset", "start over", "naya", "restart"):
        _SESSIONS.pop(session_id, None)
        return bot(
            "Namaste! 🙏 I'm Unnati.\nTell me what you harvested — "
            "e.g. *\"I have 800 kg tomato ready today from Azadpur\"*."
        )

    # Post-recommendation controls.
    if session.recommendation and normalized in ("1", "1.", "one", "join", "join load", "haan", "yes", "han", "theek hai"):
        return _handle_join(session, db)
    if session.recommendation and normalized in ("2", "2.", "two", "other", "options", "other options", "aur"):
        rec_row = db.execute(
            select(Recommendation).where(
                Recommendation.reference == session.recommendation["recommendation_id"]
            )
        ).scalar_one_or_none()
        if rec_row:
            try:
                rec = get_recommendation(db, rec_row.farmer_listing_id)
                return bot(_format_alternatives(rec), recommendation_id=rec.recommendation_id)
            except NoValidMatchError:
                pass
        return bot("No other options right now. Type *start over* to try another crop.")

    # Extract whatever we can from this message.
    rules = _rule_extract(text, db)
    llm_fields = None
    if llm_service.llm_available():
        llm_fields = llm_service.extract_fields(text)
    _merge_extraction(session, llm_fields, rules)

    missing = session.missing_fields()

    if missing:
        ack_parts = []
        if session.crop:
            ack_parts.append(f"{session.quantity_kg:.0f} kg {session.crop}" if session.quantity_kg else session.crop)
        elif session.quantity_kg:
            ack_parts.append(f"{session.quantity_kg:.0f} kg")
        if session.location_name:
            ack_parts.append(f"📍 {session.location_name}")
        ack = " ".join(ack_parts)
        prefix = f"Noted! {ack}\n" if ack else ""
        questions = {
            "crop": "Which crop are you selling? 🌱 (e.g. tomato, potato, wheat)",
            "quantity": "Great! How many kilograms are you selling?",
            "location": "Where is your farm? Village or nearest town? 📍",
            "harvest": "When was it harvested — today, yesterday, or a few days ago? 📅",
        }
        return bot(prefix + questions[missing[0]])

    return _produce_recommendation(session, db)


def cleanup_stale_sessions(max_age_seconds: float = 3600 * 12) -> None:
    cutoff = time.time() - max_age_seconds
    stale = [sid for sid, s in _SESSIONS.items() if s.updated_at < cutoff]
    for sid in stale:
        _SESSIONS.pop(sid, None)
