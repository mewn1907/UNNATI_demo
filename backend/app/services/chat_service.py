"""WhatsApp-style conversational experience (demo simulator).

Farmers talk naturally; the bot asks their preferred language (Hindi or
English), extracts crop / quantity / location / harvest, asks for missing
pieces one at a time, runs the SAME deterministic recommendation engine as
the web app, and lets the farmer join the load.

Extraction order: LLM (if enabled) → deterministic Hinglish/Hindi rules.
Recommendation presentation: LLM natural reply (if enabled) → bilingual template.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import get_close_matches

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.mandi import Mandi
from app.models.recommendation import Recommendation
from app.schemas.chat import ChatMessageOut, QuickReply
from app.schemas.recommendation import RecommendationResponse
from app.services import driver_service, llm_service
from app.services.recommendation_service import NoValidMatchError, get_recommendation, join_pool

logger = logging.getLogger("Unnati.chat")

CHAT_FARMER_NAME = "WhatsApp Demo Farmer"
CHAT_FARMER_PHONE = "+91-90000-90909"

CROP_SYNONYMS = {
    "tomato": "Tomato", "tomatoes": "Tomato", "tamatar": "Tomato", "tmatar": "Tomato",
    "टमाटर": "Tomato", "टमेटर": "Tomato",
    "potato": "Potato", "potatoes": "Potato", "aloo": "Potato", "aalu": "Potato",
    "आलू": "Potato",
    "onion": "Onion", "onions": "Onion", "pyaz": "Onion", "pyaaj": "Onion", "piyaz": "Onion",
    "प्याज़": "Onion", "प्याज": "Onion",
    "cabbage": "Cabbage", "band gobhi": "Cabbage", "patta gobhi": "Cabbage",
    "बंद गोभी": "Cabbage", "पत्ता गोभी": "Cabbage",
    "cauliflower": "Cauliflower", "phool gobhi": "Cauliflower", "gobhi": "Cauliflower",
    "फूल गोभी": "Cauliflower", "गोभी": "Cauliflower",
    "mango": "Mango", "mangoes": "Mango", "aam": "Mango",
    "आम": "Mango",
    "banana": "Banana", "bananas": "Banana", "kela": "Banana",
    "केले": "Banana", "केला": "Banana",
    "apple": "Apple", "apples": "Apple", "seb": "Apple",
    "सेब": "Apple",
    "wheat": "Wheat", "gehun": "Wheat", "kanak": "Wheat",
    "गेहूँ": "Wheat", "गेहूं": "Wheat",
    "rice": "Rice", "chawal": "Rice", "dhaan": "Rice", "dhan": "Rice",
    "चावल": "Rice", "धान": "Rice",
}

# Longest synonyms first so e.g. "फूल गोभी" wins over "गोभी".
_CROP_SYNONYM_ORDER = sorted(CROP_SYNONYMS, key=len, reverse=True)

LOCATION_EXTRA_NAMES = {
    "delhi": ("Delhi NCR", 28.6139, 77.209),
    "ncr": ("Delhi NCR", 28.6139, 77.209),
    "delhi ncr": ("Delhi NCR", 28.6139, 77.209),
    "azadpur": ("Azadpur, Delhi", 28.7056, 77.17),
    # Devanagari names for seeded villages/mandis.
    "नांगलोई": ("Nangloi", 28.683, 77.06),
    "मुंडका": ("Mundka", 28.6808, 76.9791),
    "बवाना": ("Bawana", 28.7985, 77.0374),
    "खरखौदा": ("Kharkhoda", 28.8355, 77.0203),
    "दिल्ली": ("Delhi NCR", 28.6139, 77.209),
    "अजमालपुर": ("Azadpur, Delhi", 28.7056, 77.17),
    "आजादपुर": ("Azadpur, Delhi", 28.7056, 77.17),
}

_QUANTITY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*"
    r"(quintal|quintals|kuintal|kwintal|tonne?s?|kg|kgs|kilo[s]?|kilograms?|क्विंटल|किंटल|किलो|किग्रा)?",
    re.IGNORECASE,
)
_TIME_WORDS_RE = re.compile(
    r"(?:in\s*\d+\s*(?:din|days?|hours?|hrs?|ghante)|\d+\s*(?:दिन|घंटे|घंटा)\s*(?:बाद|में))",
    re.IGNORECASE,
)
_RELATIVE_TIME_RE = re.compile(
    r"(?:(\d+)\s*(दिन|din|day|days|hours?|hrs?|ghante|घंटे|घंटा)\s*(?:बाद|में|mein|in|after))"
    r"|(?:(?:in|after)\s+(\d+)\s*(दिन|din|day|days|hours?|hrs?|ghante|घंटे|घंटा))",
    re.IGNORECASE,
)

# Devanagari digits → ASCII so quantity parsing works uniformly.
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_LANG_HI_MARKERS = re.compile(r"[\u0900-\u097F]|हिंदी|hindi", re.IGNORECASE)
_LANG_EN_MARKERS = re.compile(
    r"\b([ie][nm]?g[aeiou]*l?[aeiou]*s?h|अंग्रेज़ी|अंग्रेजी|angrezi)\b", re.IGNORECASE
)
_ROLE_FARMER_MARKERS = re.compile(r"farmer|किसान|grower|खेती", re.IGNORECASE)
_ROLE_DRIVER_MARKERS = re.compile(r"driver|ड्राइवर|चालक|truck owner|ट्रक", re.IGNORECASE)


@dataclass
class ChatSession:
    role: str | None = None  # "farmer" | "driver"; asked on first contact.
    language: str | None = None  # "en" | "hi"; asked on first contact.
    crop: str | None = None
    quantity_kg: float | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    harvested_at: datetime | None = None
    listing_id: int | None = None
    recommendation: dict | None = None
    capacity_kg: float | None = None
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


def _detect_language(text: str) -> str | None:
    if _LANG_EN_MARKERS.search(text):
        return "en"
    if _LANG_HI_MARKERS.search(text):
        return "hi"
    return None


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


def _fuzzy_crop(lowered: str) -> str | None:
    """Typo-tolerant crop match, e.g. 'tomoto', 'pyaajj', 'gobhii'."""
    best: tuple[int, str] | None = None
    for token in re.findall(r"[a-z\u0900-\u097F]+", lowered):
        if len(token) < 4:
            continue
        matches = get_close_matches(token, CROP_SYNONYMS.keys(), n=1, cutoff=0.8)
        if matches and (best is None or len(matches[0]) > best[0]):
            best = (len(matches[0]), CROP_SYNONYMS[matches[0]])
    return best[1] if best else None


def _rule_extract(text: str, db: Session) -> dict:
    """Deterministic English/Hinglish/Devanagari extraction."""
    lowered = text.lower().translate(_DEVANAGARI_DIGITS)

    crop = None
    for synonym in _CROP_SYNONYM_ORDER:
        if re.search(rf"{re.escape(synonym)}", lowered):
            crop = CROP_SYNONYMS[synonym]
            break
    if crop is None:
        crop = _fuzzy_crop(lowered)

    # Avoid capturing quantities embedded in time phrases like "in 3 days".
    searchable = _TIME_WORDS_RE.sub(" ", lowered)
    quantity_kg = None
    for match in _QUANTITY_RE.finditer(searchable):
        value, unit = float(match.group(1)), (match.group(2) or "").lower()
        if not unit and "." not in match.group(1) and len(match.group(1)) > 5:
            continue  # likely a phone number fragment
        if unit.startswith(("quintal", "kuintal", "kwintal", "क्विंटल", "किंटल")):
            quantity_kg = value * 100
        elif unit.startswith(("ton", "टन")):
            quantity_kg = value * 1000
        elif unit in ("kg", "kgs", "kilo", "kilos", "kilogram", "kilograms",
                      "किलो", "किग्रा"):
            quantity_kg = value
        elif unit == "" and value >= 20:  # bare number near crop context => kg
            quantity_kg = value
        if quantity_kg:
            break

    location = None
    index = _location_index(db)
    best_len = 0
    for key, entry in index.items():
        if re.search(rf"{re.escape(key)}", lowered) and len(key) > best_len:
            location = entry
            best_len = len(key)
    if location is None:
        # Typo-tolerant location match, e.g. 'nangloy', 'kharakhoda'.
        for token in re.findall(r"[a-z\u0900-\u097F]+", lowered):
            if len(token) < 5:
                continue
            matches = get_close_matches(token, index.keys(), n=1, cutoff=0.8)
            if matches and len(matches[0]) > best_len:
                location = index[matches[0]]
                best_len = len(matches[0])

    harvested_at = None
    now = datetime.now()
    if re.search(r"(today|aaj|abhi|just now|आज)", lowered):
        harvested_at = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if harvested_at > now:
            harvested_at = now - timedelta(hours=2)
    elif re.search(r"(yesterday|kal tha|beeta kal|बीता कल|बीते कल)", lowered):
        harvested_at = now - timedelta(days=1)
    elif re.search(r"(parso|परसों|न परसों)", lowered):
        harvested_at = now + timedelta(days=2)
    elif re.search(r"(kal|tomorrow|कल)", lowered):
        harvested_at = now + timedelta(days=1)
    else:
        relative = _RELATIVE_TIME_RE.search(lowered)
        if relative:
            amount_str = relative.group(1) or relative.group(3)
            unit_word = relative.group(2) or relative.group(4) or ""
            amount = int(amount_str)
            delta_days = amount if re.search(r"din|day|दिन", unit_word, re.I) else 0
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


# ---------------------------------------------------------------------------
# Bilingual message templates.
# ---------------------------------------------------------------------------

LANGUAGE_QUESTION = (
    "Namaste! 🙏 I'm *Unnati* — your farming copilot.\n\n"
    "आप किस भाषा में बात करना चाहेंगे?\n"
    "Which language would you like to chat in?"
)

ROLE_QUESTION = (
    "Namaste! 🙏 I'm *Unnati*.\n\n"
    "आप कौन हैं? · Who are you?\n\n"
    "🌾 *Farmer / किसान* — sell your produce\n"
    "🚚 *Truck Driver / ड्राइवर* — find loads on your route"
)

ROLE_QUICK_REPLIES = [
    QuickReply(label="🌾 Farmer / किसान", value="farmer"),
    QuickReply(label="🚚 Truck Driver / ड्राइवर", value="driver"),
]

DRIVER_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "intro": (
            "Great — let's find loads for your truck! 🚚\nHow much load can your "
            "vehicle carry? e.g. *\"2500 kg\"* or *\"5 tonne\"*."
        ),
        "language_set": "Got it — we'll continue in English. 🇬🇧",
        "ask_capacity": (
            "How much load can your vehicle carry? 🚛 e.g. *\"2500 kg\"*, "
            "*\"2 quintal\"* or *\"5 tonne\"*."
        ),
        "ask_origin": "Where do you usually start from? Village or town? 📍",
        "summary_header": "🚚 *Loads ready near you:*",
        "load_line": (
            "• {crop} — {count} farmer(s), {kg} kg ({util}% truck filled)\n"
            "  Best mandi: *{mandi}* · {dist} km · est. gross *₹{gross}*"
        ),
        "demo_note": "_Estimates use the same transport model farmers pay; prices are demo values._",
        "reply_prompt": "Type *start over* to search another route or capacity.",
        "no_loads": (
            "😔 No farmer loads within pickup range right now.\n\n"
            "Try a nearby bigger town or type *start over*."
        ),
    },
    "hi": {
        "intro": (
            "बढ़िया — आपके ट्रक के लिए लोड खोजते हैं! 🚚\nआपकी गाड़ी कितना "
            "वज़न ले जा सकती है? जैसे *\"2500 किलो\"* या *\"5 टन\"*।"
        ),
        "language_set": "ठीक है — हम हिंदी में बात करेंगे। 🙏",
        "ask_capacity": (
            "आपकी गाड़ी कितना वज़न ले जा सकती है? 🚛 जैसे *\"2500 किलो\"*, "
            "*\"2 क्विंटल\"* या *\"5 टन\"*।"
        ),
        "ask_origin": "आप आमतौर पर कहाँ से शुरू करते हैं? गाँव या कस्बा? 📍",
        "summary_header": "🚚 *आपके पास तैयार लोड:*",
        "load_line": (
            "• {crop} — {count} किसान, {kg} किलो (ट्रक {util}% भरा)\n"
            "  सबसे अच्छी मंडी: *{mandi}* · {dist} किमी · अनुमानित कमाई *₹{gross}*"
        ),
        "demo_note": "_अनुमान उसी ट्रांसपोर्ट मॉडल से हैं जो किसान देते हैं; कीमतें डेमो हैं।_",
        "reply_prompt": "दूसरा रूट या क्षमता खोजने के लिए *start over* लिखें।",
        "no_loads": (
            "😔 अभी पिकअप रेंज में कोई किसान लोड नहीं मिला।\n\n"
            "पास का बड़ा कस्बा आज़माएँ या *start over* लिखें।"
        ),
    },
}


def _dt(session: ChatSession, key: str) -> str:
    return DRIVER_STRINGS[session.language or "en"][key]

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "intro": (
            "Great — let's begin! 🌾\nTell me what you harvested — e.g. "
            "*\"I have 800 kg tomato ready today from Azadpur\"*."
        ),
        "language_set": "Got it — we'll continue in English. 🇬🇧",
        "ask_crop": "Which crop are you selling? 🌱 (e.g. tomato, potato, wheat)",
        "ask_quantity": "Great! How many kilograms are you selling?",
        "ask_location": "Where is your farm? Village or nearest town? 📍",
        "ask_harvest": "When was it harvested — today, yesterday, or a few days ago? 📅",
        "noted": "Noted!",
        "best_option": "🏆 *Best option for you:*",
        "sell_at": "Sell at *{mandi}* ({price:.0f}/kg)",
        "truck_departs": "🚚 Truck {truck} · departs {time} {return_label}",
        "return_label": "🔁 RETURN TRIP",
        "pool_line": "👨‍🌾 Pool: {count} farmers · {kg} kg loaded",
        "earn_more": "💰 You could earn *₹{gain} MORE* than your nearest mandi",
        "spoilage_high": "⏱ Spoilage risk: *{risk}* — move within ~{hours:.0f}h",
        "spoilage_med": "⏱ Spoilage watch: medium — ~{hours:.0f}h window",
        "demo_note": "_Prices are seeded demo values._",
        "reply_prompt": "Reply *1️⃣ Join this load* or *2️⃣ Other options*.",
        "alternatives_header": "Other options we found:",
        "sell_nearby": "• Sell nearby ({mandi}): ₹{net} net",
        "alt_option": "• {name}: ₹{net} net",
        "alternatives_prompt": "Reply *1️⃣ Join the recommended load* or ask me anything else.",
        "no_other_options": "No other options right now. Type *start over* to try another crop.",
        "join_confirm": (
            "✅ *Load confirmed!*\n\n{message}\n\n"
            "🚚 Truck {truck}\n🕒 Departure: {departure}\n📍 Destination: {destination}\n\n"
            "You'll get reminders before departure."
        ),
        "load_closed": "That load just closed. Let's find another option — tell me your crop again.",
        "could_not_record": "I couldn't record that: {reason}. Let's try again — what did you harvest?",
        "no_safe_load": (
            "😔 I couldn't find a safe load right now.\n\nWe checked:\n"
            "• nearby farmers\n• available trucks\n• mandi routes\n"
            "• capacity\n• spoilage timing\n\n"
            "Try increasing pickup radius or another crop day. Or type *start over*."
        ),
        "restart": (
            "Namaste! 🙏 I'm Unnati.\nTell me what you harvested — "
            "e.g. *\"I have 800 kg tomato ready today from Azadpur\"*."
        ),
        "need_language": "Please pick a language first — reply *Hindi* or *English*. 🙂",
    },
    "hi": {
        "intro": (
            "बढ़िया — चलिए शुरू करें! 🌾\nमुझे बताइए आपने क्या उगाया है — जैसे "
            "*\"आज नांगलोई से 800 किलो टमाटर तैयार है\"*।"
        ),
        "language_set": "ठीक है — हम हिंदी में बात करेंगे। 🙏",
        "ask_crop": "आप कौन सी फसल बेचना चाहते हैं? 🌱 (जैसे टमाटर, आलू, गेहूं)",
        "ask_quantity": "बढ़िया! आप कितने किलो बेचना चाहते हैं?",
        "ask_location": "आपका खेत कहाँ है? गाँव या नज़दीकी कस्बा? 📍",
        "ask_harvest": "फसल कब कटी थी — आज, बीता कल, या कुछ दिन पहले? 📅",
        "noted": "समझ गया!",
        "best_option": "🏆 *आपके लिए सबसे अच्छा विकल्प:*",
        "sell_at": "*{mandi}* में बेचें ({price:.0f}/किलो)",
        "truck_departs": "🚚 ट्रक {truck} · प्रस्थान {time} {return_label}",
        "return_label": "🔁 रिटर्न ट्रिप",
        "pool_line": "👨‍🌾 पूल: {count} किसान · {kg} किलो लोड",
        "earn_more": "💰 आप अपने नज़दीकी मंडी से *₹{gain} ज़्यादा* कमा सकते हैं",
        "spoilage_high": "⏱ खराब होने का खतरा: *{risk}* — ~{hours:.0f} घंटे में भेजें",
        "spoilage_med": "⏱ खराब होने की चेतावनी: मध्यम — ~{hours:.0f} घंटे का समय",
        "demo_note": "_कीमतें डेमो (नमूना) डेटा हैं।_",
        "reply_prompt": "*1️⃣ इस लोड से जुड़ें* या *2️⃣ अन्य विकल्प* भेजें।",
        "alternatives_header": "हमें ये अन्य विकल्प मिले:",
        "sell_nearby": "• नज़दीक में बेचें ({mandi}): ₹{net} शुद्ध",
        "alt_option": "• {name}: ₹{net} शुद्ध",
        "alternatives_prompt": "*1️⃣ सुझाए गए लोड से जुड़ें* या मुझसे कुछ और पूछें।",
        "no_other_options": "अभी कोई अन्य विकल्प नहीं है। दूसरी फसल के लिए *start over* लिखें।",
        "join_confirm": (
            "✅ *लोड कन्फर्म!*\n\n{message}\n\n"
            "🚚 ट्रक {truck}\n🕒 प्रस्थान: {departure}\n📍 गंतव्य: {destination}\n\n"
            "प्रस्थान से पहले आपको रिमाइंडर मिलेंगे।"
        ),
        "load_closed": "वह लोड अभी बंद हो गया। कोई और विकल्प खोजते हैं — फिर से बताइए आपने क्या उगाया है।",
        "could_not_record": "यह दर्ज नहीं हो सका: {reason}. चलिए फिर से — आपने क्या उगाया है?",
        "no_safe_load": (
            "😔 अभी कोई सुरक्षित लोड नहीं मिला।\n\nहमने जाँचा:\n"
            "• आस-पास के किसान\n• उपलब्ध ट्रक\n• मंडी रूट\n"
            "• क्षमता\n• खराब होने का समय\n\n"
            "पिकअप रेडियस बढ़ाकर या किसी और दिन कोशिश करें। या *start over* लिखें।"
        ),
        "restart": (
            "नमस्ते! 🙏 मैं Unnati हूँ।\nमुझे बताइए आपने क्या उगाया है — "
            "जैसे *\"आज नांगलोई से 800 किलो टमाटर तैयार है\"*।"
        ),
        "need_language": "पहले भाषा चुनें — *हिंदी* या *English* लिखें। 🙂",
    },
}


def _t(session: ChatSession, key: str) -> str:
    lang = session.language or "en"
    return STRINGS[lang][key]


def _format_recommendation(rec: RecommendationResponse, session: ChatSession) -> str:
    """LLM-presented message when available; deterministic template otherwise."""
    r = rec.recommended
    pool_count = r.pool.farmer_count if r.pool else 1
    facts = {
        "crop": rec.crop_name,
        "quantity_kg": rec.quantity_kg,
        "village": r.pool.members[0].village if r.pool and r.pool.members else "your farm",
        "recommended_mandi": r.mandi_name,
        "price_per_kg": r.price_per_kg,
        "truck": r.truck_id,
        "is_return_trip": r.is_return_trip,
        "departs": r.departure_at.strftime("%I:%M %p").lstrip("0") if r.departure_at else "",
        "pool_farmer_count": pool_count,
        "pool_total_kg": r.pool.total_quantity_kg if r.pool else rec.quantity_kg,
        "net_gain_vs_nearest_mandi": rec.net_gain,
        "spoilage_risk": rec.spoilage.risk_level,
        "hours_remaining": rec.spoilage.hours_remaining,
        "note": "prices are seeded demo values",
    }
    if llm_service.llm_available():
        reply = llm_service.chat_reply(facts, session.language or "en")
        if reply:
            footer = "\n\n" + "\n".join([_t(session, "demo_note"), _t(session, "reply_prompt")])
            return reply + footer

    # Deterministic fallback template.
    lang = session.language or "en"
    emoji = "🍅" if "tomato" in rec.crop_name.lower() else "🌾"
    if lang == "hi":
        risk_hi = {"HIGH": "उच्च", "CRITICAL": "अति-उच्च", "MEDIUM": "मध्यम",
                   "LOW": "कम"}.get(rec.spoilage.risk_level, rec.spoilage.risk_level)
        qty_line = f"{rec.quantity_kg:.0f} किलो {rec.crop_name}"
        if r.pool and r.pool.members:
            qty_line += f" · 📍 {r.pool.members[0].village}"
    else:
        risk_hi = rec.spoilage.risk_level
        qty_line = f"{rec.quantity_kg:.0f} kg {rec.crop_name}"
        if r.pool and r.pool.members:
            qty_line += f" · 📍 {r.pool.members[0].village}"
    lines = [
        ("समझ गया! " if lang == "hi" else "Got it! ") + emoji,
        qty_line,
        "",
        _t(session, "best_option"),
        _t(session, "sell_at").format(mandi=r.mandi_name, price=r.price_per_kg),
    ]
    if r.truck_id:
        lines.append(_t(session, "truck_departs").format(
            truck=r.truck_id,
            time=r.departure_at.strftime("%I:%M %p").lstrip("0"),
            return_label=_t(session, "return_label") if r.is_return_trip else "",
        ))
    if r.pool and r.pool.farmer_count > 1:
        lines.append(_t(session, "pool_line").format(
            count=r.pool.farmer_count,
            kg=f"{r.pool.total_quantity_kg:,.0f}",
        ))
    if rec.net_gain > 0:
        lines.append("")
        lines.append(_t(session, "earn_more").format(gain=f"{rec.net_gain:,.0f}"))
    risk = rec.spoilage.risk_level
    display_risk = risk_hi if lang == "hi" else risk
    if risk in ("HIGH", "CRITICAL"):
        lines.append(_t(session, "spoilage_high").format(
            risk=display_risk, hours=rec.spoilage.hours_remaining))
    elif risk == "MEDIUM":
        lines.append(_t(session, "spoilage_med").format(hours=rec.spoilage.hours_remaining))
    lines.append("")
    lines.append(_t(session, "demo_note"))
    lines.append(_t(session, "reply_prompt"))
    return "\n".join(lines)


def _format_alternatives(rec: RecommendationResponse, session: ChatSession) -> str:
    lines = [_t(session, "alternatives_header"), ""]
    baseline_net = rec.baseline.net_profit
    lines.append(_t(session, "sell_nearby").format(
        mandi=rec.baseline.mandi_name, net=f"{baseline_net:,.0f}"))
    options = [(rec.recommended.mandi_name, rec.recommended.net_profit)] + [
        (alt.mandi_name, alt.net_profit) for alt in rec.alternatives
    ]
    for name, net in options:
        lines.append(_t(session, "alt_option").format(name=name, net=f"{net:,.0f}"))
    lines.append("")
    lines.append(_t(session, "alternatives_prompt"))
    return "\n".join(lines)


def _handle_join(session: ChatSession, db: Session) -> ChatMessageOut:
    rec_data = session.recommendation
    if not rec_data or not rec_data.get("pool_id"):
        return bot(_t(session, "restart"))
    try:
        result = join_pool(db, rec_data["pool_id"], rec_data["listing_id"])
    except LookupError:
        return bot(_t(session, "load_closed"))
    departure = result.departure_at.strftime("%d %b · %I:%M %p").lstrip("0")
    session.joined = True
    return bot(
        _t(session, "join_confirm").format(
            message=result.message,
            truck=result.truck_id,
            departure=departure,
            destination=result.destination_mandi,
        ),
        quick_replies=[QuickReply(label="Start over / नया शुरू", value="start over")],
        joined=True,
    )


def _produce_recommendation(session: ChatSession, db: Session) -> ChatMessageOut:
    try:
        listing = _create_listing_from_session(db, session)
    except ValueError as exc:
        return bot(_t(session, "could_not_record").format(reason=exc))
    session.listing_id = listing.id

    try:
        rec = get_recommendation(db, listing.id)
    except NoValidMatchError:
        session.crop = None
        session.quantity_kg = None
        return bot(_t(session, "no_safe_load"))

    session.recommendation = {
        "recommendation_id": rec.recommendation_id,
        "listing_id": listing.id,
        "pool_id": _pool_id_for(db, rec.recommendation_id),
    }
    return bot(
        _format_recommendation(rec, session),
        quick_replies=[
            QuickReply(label="1 - Join load / जुड़ें", value="1"),
            QuickReply(label="2 - Other options / अन्य विकल्प", value="2"),
            QuickReply(label="Start over / नया शुरू", value="start over"),
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


_RESET_WORDS = {"reset", "start over", "naya", "restart", "नया शुरू", "दोबारा शुरू"}
_JOIN_WORDS = {"1", "1.", "one", "join", "join load", "haan", "yes", "han", "theek hai", "haan ji", "हाँ", "जी"}
_OTHER_WORDS = {"2", "2.", "two", "other", "options", "other options", "aur", "और", "अन्य"}

_DRIVER_START_OVER_QR = [QuickReply(label="Start over / नया शुरू", value="start over")]


def _format_driver_summary(session: ChatSession, db: Session) -> ChatMessageOut:
    try:
        opportunities = driver_service.find_opportunities(
            db, session.latitude, session.longitude, float(session.capacity_kg)
        )
    except ValueError:
        return bot(_dt(session, "no_loads"), quick_replies=_DRIVER_START_OVER_QR)
    if not opportunities:
        return bot(_dt(session, "no_loads"), quick_replies=_DRIVER_START_OVER_QR)

    lines = [_dt(session, "summary_header"), ""]
    for o in opportunities[:3]:
        lines.append(_dt(session, "load_line").format(
            crop=o.crop,
            count=o.load_count,
            kg=f"{o.total_kg:,.0f}",
            util=o.utilization_pct,
            mandi=o.best_option.mandi_name,
            dist=o.best_option.distance_km,
            gross=f"{o.best_option.est_gross_inr:,.0f}",
        ))
    deterministic = "\n".join(lines)

    if llm_service.llm_available():
        reply = llm_service.driver_reply(
            driver_service.driver_facts(opportunities[0]), session.language or "en"
        )
        if reply:
            footer = "\n\n" + "\n".join(
                [_dt(session, "demo_note"), _dt(session, "reply_prompt")])
            deterministic = reply + footer

    return bot(deterministic, quick_replies=_DRIVER_START_OVER_QR)


def _handle_driver_message(session: ChatSession, db: Session, text: str) -> ChatMessageOut:
    rules = _rule_extract(text, db)
    if session.capacity_kg is None:
        qty = rules["quantity_kg"]
        if qty and 100 <= qty <= 50_000:
            session.capacity_kg = qty
        else:
            return bot(_dt(session, "ask_capacity"))
    if session.location_name is None:
        if rules["location"]:
            display, lat, lng = rules["location"]
            session.location_name = display
            session.latitude, session.longitude = lat, lng
        else:
            llm_fields = None
            if llm_service.llm_available():
                llm_fields = llm_service.extract_fields(text)
            _merge_extraction(session, llm_fields, {
                **rules,
                "crop": None,
                "quantity_kg": None,
                "harvested_at": None,
            })
            if session.location_name is None or session.latitude is None:
                return bot(_dt(session, "ask_origin"))
    return _format_driver_summary(session, db)


def handle_message(db: Session, session_id: str, text: str) -> ChatMessageOut:
    """Main conversational turn handler with Hindi/English language selection."""
    normalized = text.strip().lower()
    session = _get_session(session_id)

    if normalized in _RESET_WORDS:
        _SESSIONS.pop(session_id, None)
        session = _get_session(session_id)
        return bot(ROLE_QUESTION, quick_replies=ROLE_QUICK_REPLIES)

    # Role gate — every conversation starts with farmer vs truck driver.
    if session.role is None:
        detected_role = None
        if _ROLE_FARMER_MARKERS.search(text) and not _ROLE_DRIVER_MARKERS.search(text):
            detected_role = "farmer"
        elif _ROLE_DRIVER_MARKERS.search(text):
            detected_role = "driver"
        if detected_role is None:
            return bot(ROLE_QUESTION, quick_replies=ROLE_QUICK_REPLIES)
        session.role = detected_role
        lang = _detect_language(text)
        if lang is not None:
            session.language = lang
            intro = _t(session, "intro") if detected_role == "farmer" else _dt(session, "intro")
            return bot("\n\n".join([_t(session, "language_set"), intro]))

    # Language selection gate — always resolved before the produce flow.
    detected = _detect_language(text)
    if session.language is None:
        if detected is None:
            return bot(LANGUAGE_QUESTION + "\n\n" + STRINGS["en"]["need_language"],
                       quick_replies=[
                           QuickReply(label="हिंदी", value="हिंदी"),
                           QuickReply(label="English", value="English"),
                       ])
        session.language = detected
        # If the message was ONLY the language choice, confirm + show intro.
        stripped = _LANG_EN_MARKERS.sub(" ", normalized)
        stripped = _LANG_HI_MARKERS.sub(" ", stripped).strip()
        if not stripped or stripped in ("hi", "en"):
            intro = _t(session, "intro") if session.role == "farmer" else _dt(session, "intro")
            return bot("\n\n".join([_t(session, "language_set"), intro]))

    # Allow switching language mid-conversation by naming it explicitly.
    elif detected is not None and detected != session.language:
        remainder = normalized
        if detected == "en":
            remainder = _LANG_EN_MARKERS.sub(" ", remainder)
        else:
            remainder = re.sub(r"(हिंदी|\bhindi\b)", " ", remainder)
        if len(remainder.strip()) <= 4:
            session.language = detected
            intro = _t(session, "intro") if session.role == "farmer" else _dt(session, "intro")
            return bot("\n\n".join([_t(session, "language_set"), intro]))

    if session.role == "driver":
        return _handle_driver_message(session, db, text)

    # Post-recommendation controls.
    if session.recommendation and normalized in _JOIN_WORDS:
        return _handle_join(session, db)
    if session.recommendation and normalized in _OTHER_WORDS:
        rec_row = db.execute(
            select(Recommendation).where(
                Recommendation.reference == session.recommendation["recommendation_id"]
            )
        ).scalar_one_or_none()
        if rec_row:
            try:
                rec = get_recommendation(db, rec_row.farmer_listing_id)
                return bot(
                    _format_alternatives(rec, session),
                    recommendation_id=rec.recommendation_id,
                )
            except NoValidMatchError:
                pass
        return bot(_t(session, "no_other_options"))

    # Extract whatever we can from this message.
    rules = _rule_extract(text, db)
    llm_fields = None
    if llm_service.llm_available():
        context = {
            "known_crop": session.crop,
            "known_quantity_kg": session.quantity_kg,
            "known_location": session.location_name,
        }
        llm_fields = llm_service.extract_fields(text, context)
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
        prefix = f"{_t(session, 'noted')} {ack}\n" if ack else ""
        questions = {
            "crop": _t(session, "ask_crop"),
            "quantity": _t(session, "ask_quantity"),
            "location": _t(session, "ask_location"),
            "harvest": _t(session, "ask_harvest"),
        }
        return bot(prefix + questions[missing[0]])

    return _produce_recommendation(session, db)


def cleanup_stale_sessions(max_age_seconds: float = 3600 * 12) -> None:
    cutoff = time.time() - max_age_seconds
    stale = [sid for sid, s in _SESSIONS.items() if s.updated_at < cutoff]
    for sid in stale:
        _SESSIONS.pop(sid, None)
