"""Driver-side opportunity finder.

Mirrors the farmer flow: given where a truck driver is based and the vehicle
capacity, deterministic rules select nearby AVAILABLE farmer loads and estimate
the gross transport revenue using the SAME transport cost model the farmers
pay (no numbers are invented here).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.engines.transport_engine import calculate_transport_cost
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.mandi import Mandi
from app.services.matching_service import price_map_for_crop, road_km
from app.utils.geo import haversine_km

DRIVER_PICKUP_RADIUS_KM = 60.0


@dataclass
class DriverLoad:
    listing_id: int
    farmer_name: str
    village: str
    crop: str
    quantity_kg: float
    distance_km: float


@dataclass
class MandiOption:
    mandi_name: str
    distance_km: float
    price_per_kg: float
    est_gross_inr: float


@dataclass
class DriverOpportunity:
    crop: str
    total_kg: float
    load_count: int
    utilization_pct: float
    best_option: MandiOption
    other_options: list[MandiOption] = field(default_factory=list)
    loads: list[DriverLoad] = field(default_factory=list)


def find_opportunities(
    db: Session,
    origin_lat: float,
    origin_lng: float,
    capacity_kg: float,
    radius_km: float | None = None,
) -> list[DriverOpportunity]:
    """Rank crop-specific load bundles near the driver by estimated gross."""
    if capacity_kg <= 0:
        raise ValueError("capacity_kg must be positive")
    radius = radius_km if radius_km is not None else DRIVER_PICKUP_RADIUS_KM

    rows = db.execute(
        select(FarmerListing, Farmer, Crop)
        .join(Farmer, FarmerListing.farmer_id == Farmer.id)
        .join(Crop, FarmerListing.crop_id == Crop.id)
        .where(
            FarmerListing.status == "AVAILABLE",
            FarmerListing.quantity_kg >= settings.MIN_LISTING_QUANTITY_KG,
        )
    ).all()

    by_crop: dict[int, list[tuple[FarmerListing, Farmer, Crop, float]]] = {}
    for listing, farmer, crop in rows:
        dist = haversine_km(origin_lat, origin_lng, listing.latitude, listing.longitude)
        if dist > radius:
            continue
        by_crop.setdefault(crop.id, []).append((listing, farmer, crop, dist))

    opportunities: list[DriverOpportunity] = []
    for crop_id, candidates in by_crop.items():
        candidates.sort(key=lambda item: item[3])
        selected: list[tuple[FarmerListing, Farmer, Crop, float]] = []
        filled = 0.0
        for item in candidates:
            if filled + item[0].quantity_kg <= capacity_kg + 1e-9:
                selected.append(item)
                filled += item[0].quantity_kg
        if not selected or filled <= 0:
            continue

        prices = price_map_for_crop(db, crop_id)
        options: list[MandiOption] = []
        for mandi in db.execute(select(Mandi)).scalars().all():
            price = prices.get(mandi.id)
            if not price or price <= 0:
                continue
            dist = road_km(origin_lat, origin_lng, mandi.latitude, mandi.longitude)
            gross = calculate_transport_cost(
                distance_km=dist,
                farmer_quantity_kg=filled,
                total_pool_quantity_kg=filled,
                return_trip=False,
            ).effective_total_cost
            options.append(MandiOption(
                mandi_name=mandi.name,
                distance_km=dist,
                price_per_kg=price,
                est_gross_inr=round(gross),
            ))
        if not options:
            continue
        options.sort(key=lambda o: o.est_gross_inr, reverse=True)

        _, _, crop, _ = selected[0]
        opportunities.append(DriverOpportunity(
            crop=crop.name,
            total_kg=round(filled),
            load_count=len(selected),
            utilization_pct=round(filled / capacity_kg * 100),
            best_option=options[0],
            other_options=options[1:4],
            loads=[
                DriverLoad(
                    listing_id=listing.id,
                    farmer_name=farmer.name,
                    village=farmer.village,
                    crop=crop.name,
                    quantity_kg=listing.quantity_kg,
                    distance_km=round(dist, 1),
                )
                for listing, farmer, crop, dist in selected
            ],
        ))

    opportunities.sort(key=lambda o: o.best_option.est_gross_inr, reverse=True)
    return opportunities


def driver_facts(opportunity: DriverOpportunity) -> dict:
    """Flat validated facts for LLM presentation (LLM never computes these)."""
    return {
        "crop": opportunity.crop,
        "load_count": opportunity.load_count,
        "total_kg": opportunity.total_kg,
        "utilization_pct": opportunity.utilization_pct,
        "best_mandi": opportunity.best_option.mandi_name,
        "distance_km": opportunity.best_option.distance_km,
        "price_per_kg": opportunity.best_option.price_per_kg,
        "est_gross_inr": opportunity.best_option.est_gross_inr,
        "note": "estimates use the same transport model farmers pay; prices are seeded demo values",
    }
