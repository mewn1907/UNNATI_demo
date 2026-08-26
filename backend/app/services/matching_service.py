"""Matching engine: who can I pool with, which truck, where to sell?

All logic here is deterministic and rule-driven. The LLM never participates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.engines.capacity_engine import CapacityResult, check_capacity
from app.engines.profit_engine import ProfitBreakdown, calculate_profit
from app.engines.spoilage_engine import calculate_spoilage_risk
from app.engines.transport_engine import TransportBreakdown, calculate_transport_cost
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.mandi import Mandi
from app.models.mandi_price import MandiPrice
from app.models.truck import Truck
from app.models.truck_route import TruckRoute
from app.services.weather_service import WeatherConditions, get_conditions
from app.utils.geo import haversine_km
from app.utils.time import hours_between

logger = logging.getLogger("Unnati.matching")

# Road distances are longer than great-circle distances.
ROAD_FACTOR = 1.25
# Average mixed rural/highway speed used for travel-time estimates.
AVG_SPEED_KMH = 30.0
# How far a truck origin may be from the farmer for pickup feasibility.
TRUCK_ORIGIN_RADIUS_KM = 80.0
# Beyond this estimated loss the trip is rejected outright (hard constraint).
MAX_ACCEPTABLE_LOSS_PCT = 60.0


@dataclass(frozen=True)
class CompatibleListing:
    listing: FarmerListing
    farmer: Farmer
    distance_km: float


@dataclass
class PoolComposition:
    members: list[CompatibleListing]
    total_quantity_kg: float
    remaining_capacity_kg: float
    utilization: float


@dataclass
class Candidate:
    candidate_id: str
    route: TruckRoute
    truck: Truck
    mandi: Mandi
    price_per_kg: float
    quantity_kg: float
    pool: PoolComposition
    transport: TransportBreakdown
    solo_transport_same_leg: float
    spoilage_pct_at_arrival: float
    spoilage_hours_remaining_at_departure: float
    profit: ProfitBreakdown
    valid: bool = True
    rejection_reason: str | None = None


def road_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return round(haversine_km(lat1, lon1, lat2, lon2) * ROAD_FACTOR, 1)


def price_map_for_crop(db: Session, crop_id: int) -> dict[int, float]:
    rows = db.execute(
        select(MandiPrice)
        .where(MandiPrice.crop_id == crop_id)
        .order_by(MandiPrice.recorded_at)
    ).scalars().all()
    return {row.mandi_id: row.price_per_kg for row in rows}


def find_compatible_listings(
    db: Session, target: FarmerListing, radius_km: float | None = None
) -> list[CompatibleListing]:
    """Same-crop, nearby, similar-harvest-time AVAILABLE listings."""
    max_radius = radius_km if radius_km is not None else settings.MAX_POOL_RADIUS_KM

    rows = db.execute(
        select(FarmerListing, Farmer)
        .join(Farmer, FarmerListing.farmer_id == Farmer.id)
        .where(
            FarmerListing.crop_id == target.crop_id,
            FarmerListing.id != target.id,
            FarmerListing.status == "AVAILABLE",
            FarmerListing.quantity_kg >= settings.MIN_LISTING_QUANTITY_KG,
        )
    ).all()

    compatible: list[CompatibleListing] = []
    for listing, farmer in rows:
        harvest_diff = abs(hours_between(target.harvested_at, listing.harvested_at))
        if harvest_diff > settings.MAX_HARVEST_TIME_DIFF_HOURS:
            continue
        distance = haversine_km(target.latitude, target.longitude, listing.latitude, listing.longitude)
        if distance > max_radius:
            continue
        compatible.append(CompatibleListing(listing, farmer, round(distance, 1)))

    compatible.sort(key=lambda c: c.distance_km)
    return compatible


def build_pool(
    target: FarmerListing,
    target_farmer: Farmer,
    compatible: list[CompatibleListing],
    available_capacity_kg: float,
) -> PoolComposition | None:
    """Greedy fill: target always included; nearest neighbours added first.

    Returns None when even the target's own load exceeds capacity.
    """
    if target.quantity_kg <= 0 or target.quantity_kg > available_capacity_kg + 1e-9:
        return None

    kept: list[CompatibleListing] = []
    total = target.quantity_kg
    for item in compatible:
        if total + item.listing.quantity_kg <= available_capacity_kg + 1e-9:
            kept.append(item)
            total += item.listing.quantity_kg

    members = [CompatibleListing(target, target_farmer, 0.0), *kept]
    return PoolComposition(
        members=members,
        total_quantity_kg=total,
        remaining_capacity_kg=max(0.0, available_capacity_kg - total),
        utilization=total / available_capacity_kg,
    )


def _spoilage_at(
    crop: Crop,
    listing: FarmerListing,
    when: datetime,
    conditions: WeatherConditions,
) -> tuple[float, float]:
    """Returns (estimated_loss_pct, hours_remaining)."""
    risk = calculate_spoilage_risk(
        crop, listing.harvested_at, when, conditions.temperature_c, conditions.humidity_pct
    )
    return risk.estimated_loss_percentage, risk.hours_remaining


def generate_candidates(
    db: Session,
    listing: FarmerListing,
    now: datetime,
    preferred_radius_km: float | None = None,
) -> tuple[list[Candidate], dict[int, float], WeatherConditions]:
    """Generate and hard-constraint-validate truck+mandi+pooled-load candidates."""
    crop = db.get(Crop, listing.crop_id)
    farmer = db.get(Farmer, listing.farmer_id)
    if crop is None or farmer is None:
        raise ValueError("listing is missing crop or farmer data")

    prices = price_map_for_crop(db, listing.crop_id)
    conditions = get_conditions(listing.latitude, listing.longitude, farmer.state)
    compatible = find_compatible_listings(db, listing, preferred_radius_km)

    route_rows = db.execute(
        select(TruckRoute, Truck)
        .join(Truck, TruckRoute.truck_id == Truck.id)
        .where(Truck.status == "AVAILABLE", TruckRoute.departure_at > now)
    ).all()

    candidates: list[Candidate] = []

    for route, truck in route_rows:
        price = prices.get(route.destination_mandi_id) if route.destination_mandi_id else None
        if price is None or price <= 0:
            continue  # hard constraint: no mandi price

        origin_gap = haversine_km(
            listing.latitude, listing.longitude, route.origin_latitude, route.origin_longitude
        )
        if origin_gap > TRUCK_ORIGIN_RADIUS_KM:
            continue  # hard constraint: outside allowed pickup range

        pool = build_pool(listing, farmer, compatible, truck.available_capacity_kg)
        if pool is None:
            continue  # hard constraint: even solo load exceeds truck capacity

        arrival = route.estimated_arrival_at
        loss_pct, _ = _spoilage_at(crop, listing, arrival, conditions)
        _, hours_left_at_departure = _spoilage_at(crop, listing, route.departure_at, conditions)

        transport = calculate_transport_cost(
            distance_km=route.distance_km,
            farmer_quantity_kg=listing.quantity_kg,
            total_pool_quantity_kg=pool.total_quantity_kg,
            return_trip=route.return_available,
        )

        solo_transport = calculate_transport_cost(
            distance_km=route.distance_km,
            farmer_quantity_kg=listing.quantity_kg,
            return_trip=False,
        ).effective_total_cost

        profit = calculate_profit(
            quantity_kg=listing.quantity_kg,
            price_per_kg=price,
            transport_cost=transport.farmer_share,
            spoilage_percentage=loss_pct,
        )

        candidate = Candidate(
            candidate_id=f"{route.id}",
            route=route,
            truck=truck,
            mandi=db.get(Mandi, route.destination_mandi_id),
            price_per_kg=price,
            quantity_kg=listing.quantity_kg,
            pool=pool,
            transport=transport,
            solo_transport_same_leg=solo_transport,
            spoilage_pct_at_arrival=loss_pct,
            spoilage_hours_remaining_at_departure=hours_left_at_departure,
            profit=profit,
        )
        _apply_hard_constraints(candidate)
        candidates.append(candidate)

    valid_count = sum(1 for c in candidates if c.valid)
    logger.info("Generated %d candidates (%d valid) for listing %s",
                len(candidates), valid_count, listing.id)
    return candidates, prices, conditions


def _apply_hard_constraints(candidate: Candidate) -> None:
    if candidate.quantity_kg <= 0:
        candidate.valid = False
        candidate.rejection_reason = "quantity must be positive"
    elif candidate.spoilage_hours_remaining_at_departure <= 0:
        candidate.valid = False
        candidate.rejection_reason = "departs after the estimated spoilage window closes"
    elif candidate.spoilage_pct_at_arrival >= MAX_ACCEPTABLE_LOSS_PCT:
        candidate.valid = False
        candidate.rejection_reason = (
            f"estimated spoilage loss {candidate.spoilage_pct_at_arrival:.0f}% before "
            "arrival makes this trip uneconomical"
        )


def compute_baseline(
    db: Session, listing: FarmerListing, now: datetime
) -> tuple[Mandi, float, TransportBreakdown, ProfitBreakdown, WeatherConditions]:
    """Nearest priced mandi sold solo with own transport — the 'sell normally' option."""
    crop = db.get(Crop, listing.crop_id)
    farmer = db.get(Farmer, listing.farmer_id)
    if crop is None or farmer is None:
        raise ValueError("listing is missing crop or farmer data")

    prices = price_map_for_crop(db, listing.crop_id)
    conditions = get_conditions(listing.latitude, listing.longitude, farmer.state)

    mandis = db.execute(select(Mandi)).scalars().all()
    feasible = [(m, prices[m.id]) for m in mandis if m.id in prices]
    if not feasible:
        raise ValueError("no mandi price available for this crop")

    def mandi_distance(m: Mandi) -> float:
        return road_km(listing.latitude, listing.longitude, m.latitude, m.longitude)

    feasible.sort(key=lambda pair: mandi_distance(pair[0]))
    mandi, price = feasible[0]

    distance = mandi_distance(mandi)
    travel_hours = distance / AVG_SPEED_KMH
    loss_pct, _ = _spoilage_at(crop, listing, now + timedelta(hours=travel_hours), conditions)

    transport = calculate_transport_cost(
        distance_km=distance,
        farmer_quantity_kg=listing.quantity_kg,
        return_trip=False,
    )
    profit = calculate_profit(
        quantity_kg=listing.quantity_kg,
        price_per_kg=price,
        transport_cost=transport.effective_total_cost,
        spoilage_percentage=loss_pct,
    )
    return mandi, price, transport, profit, conditions
