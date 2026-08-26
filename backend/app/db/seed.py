"""Idempotent database seeding with the golden hackathon demo scenario.

Run manually:
    python -m app.db.seed

The seeder is safe to re-run: it wipes demo tables first so departure times
stay relative to "today" no matter when the demo is launched.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, time as dtime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.db.base import Base, create_all
from app.db.database import SessionLocal, engine
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.mandi import Mandi
from app.models.mandi_price import MandiPrice
from app.models.notification import Notification
from app.models.pool_member import PoolMember
from app.models.recommendation import Recommendation
from app.models.truck import Truck
from app.models.truck_route import TruckRoute

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

MODELS_IN_SEED_ORDER = (
    PoolMember,
    Recommendation,
    Notification,
    FarmerListing,
    TruckRoute,
    Truck,
    MandiPrice,
    Mandi,
    Crop,
    Farmer,
)


def _load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8-sig"))


def _today_at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(datetime.now().date(), dtime(hour, minute))


def _next_occurrence(hour: int, minute: int = 0) -> datetime:
    """Today at hh:mm, or tomorrow when that time already passed.

    Keeps demo departures in the future no matter when seeding runs.
    """
    target = _today_at(hour, minute)
    if target <= datetime.now() + timedelta(minutes=30):
        target += timedelta(days=1)
    return target


def seed() -> None:
    create_all()

    crops_data = _load("crops.json")
    mandis_data = _load("mandis.json")
    farmers_data = _load("farmers.json")
    trucks_data = _load("trucks.json")

    with SessionLocal() as db:
        # Wipe previous demo data so re-seeding is deterministic.
        for model in MODELS_IN_SEED_ORDER:
            db.query(model).delete()
        db.commit()

        crops_by_name: dict[str, Crop] = {}
        for spec in crops_data["crops"]:
            crop = Crop(**spec)
            db.add(crop)
            crops_by_name[spec["name"]] = crop

        mandis_by_name: dict[str, Mandi] = {}
        for spec in mandis_data["mandis"]:
            mandi = Mandi(
                id=spec["id"],
                name=spec["name"],
                city=spec["city"],
                district=spec["district"],
                state=spec["state"],
                latitude=spec["latitude"],
                longitude=spec["longitude"],
            )
            db.add(mandi)
            mandis_by_name[spec["name"]] = mandi
        db.flush()

        price_rows = []
        for crop_name, by_mandi in mandis_data["prices_per_kg"].items():
            crop = crops_by_name[crop_name]
            for mandi_name, price in by_mandi.items():
                mandi = mandis_by_name[mandi_name]
                for days_ago in range(6, -1, -1):
                    if days_ago == 0:
                        day_price = price
                    else:
                        wave = math.sin(days_ago * 1.7 + mandi.id * 0.9 + crop.id)
                        day_price = round(price * (1 + 0.05 * wave), 2)
                    price_rows.append(
                        MandiPrice(
                            mandi_id=mandi.id, crop_id=crop.id,
                            price_per_kg=day_price, source="seeded_demo",
                            confidence=0.9,
                            recorded_at=_today_at(6) - timedelta(days=days_ago),
                        )
                    )
        db.add_all(price_rows)

        farmers_by_id: dict[int, Farmer] = {}
        for spec in farmers_data["farmers"]:
            farmer = Farmer(
                id=spec["id"], name=spec["name"], phone=spec["phone"],
                village=spec["village"], district=spec["district"], state=spec["state"],
                latitude=spec["latitude"], longitude=spec["longitude"],
            )
            db.add(farmer)
            farmers_by_id[spec["id"]] = farmer
        db.flush()

        now = datetime.now()
        listings_by_farmer: dict[int, FarmerListing] = {}
        for spec in farmers_data["listings"]:
            offset = spec.get("harvest_offset_hours_ago")
            if offset is not None:
                harvested_at = now - timedelta(hours=float(offset))
            else:
                hour, minute = (int(x) for x in spec["harvest_time"].split(":"))
                harvested_at = _today_at(hour, minute)
                if harvested_at > now:  # never seed a harvest "in the future"
                    harvested_at -= timedelta(days=1)
            listing = FarmerListing(
                farmer_id=spec["farmer_id"],
                crop_id=crops_by_name[spec["crop"]].id,
                quantity_kg=spec["quantity_kg"],
                harvested_at=harvested_at,
                available_until=harvested_at + timedelta(days=3),
                latitude=farmers_by_id[spec["farmer_id"]].latitude,
                longitude=farmers_by_id[spec["farmer_id"]].longitude,
                status=spec.get("status", "AVAILABLE"),
            )
            db.add(listing)
            listings_by_farmer[spec["farmer_id"]] = listing
        db.flush()

        for spec in trucks_data["trucks"]:
            db.add(Truck(**spec))

        route_count = 0
        for spec in trucks_data["routes"]:
            # Departures are anchored relative to seeding time so the golden
            # scenario produces identical economics no matter when it runs.
            departure = now + timedelta(hours=float(spec["departure_offset_hours"]))
            arrival = departure + timedelta(hours=float(spec["travel_hours"]))
            db.add(
                TruckRoute(
                    id=spec["id"],
                    truck_id=spec["truck_id"],
                    origin_name=spec["origin_name"],
                    origin_latitude=spec["origin_latitude"],
                    origin_longitude=spec["origin_longitude"],
                    destination_mandi_id=spec["destination_mandi_id"],
                    departure_at=departure,
                    estimated_arrival_at=arrival,
                    return_available=spec["return_available"],
                    return_destination_region=spec["return_destination_region"],
                    distance_km=spec["distance_km"],
                    estimated_cost=spec["estimated_cost"],
                )
            )
            route_count += 1

        db.commit()

        counts = {
            "farmers": db.scalar(select(Farmer.id).order_by(Farmer.id.desc()).limit(1)) or 0,
            "listings": len(listings_by_farmer),
            "crops": len(crops_by_name),
            "mandis": len(mandis_by_name),
            "trucks": len(trucks_data["trucks"]),
            "routes": route_count,
            "prices": len(price_rows),
        }

    print("Seed complete.")
    print(f"Farmers: {counts['farmers']}")
    print(f"Listings: {counts['listings']}")
    print(f"Crops: {counts['crops']}")
    print(f"Mandis: {counts['mandis']} | Trucks: {counts['trucks']} | Routes: {counts['routes']}")
    print(f"Price records: {counts['prices']}")


def reset_database_file() -> None:
    """Drop and recreate all tables (used by /api/demo/reset)."""
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    if settings.DEMO_MODE:
        seed()
    else:
        raise SystemExit("Seeding is only allowed when DEMO_MODE=true")
