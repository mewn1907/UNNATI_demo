"""Recommendation pipeline:

listing → candidates → calculations → hard constraints → ranking
        → best valid option → LLM explanation (with fallback) → response.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.ranking_engine import CandidateMetrics, rank_candidates
from app.engines.spoilage_engine import calculate_spoilage_risk
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.load_pool import LoadPool
from app.models.mandi import Mandi
from app.models.pool_member import PoolMember
from app.models.recommendation import Recommendation
from app.models.truck import Truck
from app.schemas.recommendation import (
    CandidateOption,
    JoinPoolResponse,
    OptionEconomics,
    PoolInfo,
    PoolMemberInfo,
    RecommendationResponse,
    SpoilageInfo,
)
from app.services import llm_service
from app.services.matching_service import (
    Candidate,
    compute_baseline,
    generate_candidates,
)
from app.services.notification_service import notify_pool_confirmed

logger = logging.getLogger("Unnati.recommendation")

MAX_ALTERNATIVES = 2


class NoValidMatchError(Exception):
    """Raised when no valid candidate exists for a listing."""


def _baseline_economics(
    mandi: Mandi,
    price_per_kg: float,
    distance_km: float,
    profit,
) -> OptionEconomics:
    return OptionEconomics(
        mandi_id=mandi.id,
        mandi_name=mandi.name,
        price_per_kg=price_per_kg,
        distance_km=distance_km,
        gross_revenue=round(profit.gross_revenue),
        transport_cost=round(profit.transport_cost),
        spoilage_loss=round(profit.spoilage_loss),
        spoilage_percentage=profit.spoilage_percentage,
        net_profit=round(profit.net_profit),
    )


def _candidate_to_option(candidate: Candidate, score: float) -> CandidateOption:
    pool = PoolInfo(
        farmer_count=len(candidate.pool.members),
        total_quantity_kg=round(candidate.pool.total_quantity_kg),
        remaining_capacity_kg=round(candidate.pool.remaining_capacity_kg),
        utilization_percent=round(candidate.pool.utilization * 100),
        members=[
            PoolMemberInfo(
                farmer_name=m.farmer.name,
                village=m.farmer.village,
                quantity_kg=m.listing.quantity_kg,
                distance_km=m.distance_km,
            )
            for m in candidate.pool.members
        ],
    )
    return CandidateOption(
        candidate_id=candidate.candidate_id,
        mandi_id=candidate.mandi.id if candidate.mandi else None,
        mandi_name=candidate.mandi.name if candidate.mandi else "Unknown",
        price_per_kg=candidate.price_per_kg,
        distance_km=candidate.route.distance_km,
        truck_id=candidate.truck.id,
        truck_registration=candidate.truck.registration_number,
        is_return_trip=candidate.route.return_available,
        departure_at=candidate.route.departure_at,
        gross_revenue=round(candidate.profit.gross_revenue),
        transport_cost=round(candidate.profit.transport_cost),
        spoilage_loss=round(candidate.profit.spoilage_loss),
        spoilage_percentage=candidate.spoilage_pct_at_arrival,
        net_profit=round(candidate.profit.net_profit),
        pool=pool,
        score=score,
    )


def get_recommendation(db: Session, listing_id: int) -> RecommendationResponse:
    started = time.perf_counter()
    now = datetime.now()

    listing = db.get(FarmerListing, listing_id)
    if listing is None:
        raise LookupError(f"listing {listing_id} not found")
    crop = db.get(Crop, listing.crop_id)

    baseline_mandi, baseline_price, baseline_transport, baseline_profit, conditions = (
        compute_baseline(db, listing, now)
    )
    candidates, _prices, conditions = generate_candidates(db, listing, now)

    valid_candidates = [c for c in candidates if c.valid]
    if not valid_candidates:
        raise NoValidMatchError(
            "No suitable truck and mandi combination was found before the "
            "estimated spoilage window."
        )

    metrics = [
        CandidateMetrics(
            candidate_id=c.candidate_id,
            net_gain=c.profit.net_profit - baseline_profit.net_profit,
            pooling_benefit=(
                c.solo_transport_same_leg
                - c.transport.effective_total_cost * (c.quantity_kg / c.pool.total_quantity_kg)
            ),
            utilization=c.pool.utilization,
            is_return_trip=c.route.return_available,
            hours_remaining=c.spoilage_hours_remaining_at_departure,
            distance_km=c.route.distance_km,
        )
        for c in valid_candidates
    ]
    scores = rank_candidates(metrics)
    ranked = sorted(valid_candidates, key=lambda c: scores[c.candidate_id], reverse=True)
    best = ranked[0]
    best_score = scores[best.candidate_id]

    net_gain_value = round(best.profit.net_profit - baseline_profit.net_profit, 0)
    crop_age_hours = max(0.0, (now - listing.harvested_at).total_seconds() / 3600)

    # Persist recommendation + an OPEN load pool so "Join This Load" has a target.
    next_rec_number = (
        db.scalar(select(Recommendation.id).order_by(Recommendation.id.desc()).limit(1)) or 0
    ) + 1
    reference = f"REC-{1000 + next_rec_number}"

    pool = LoadPool(
        truck_id=best.truck.id,
        destination_mandi_id=best.mandi.id,
        total_quantity_kg=best.pool.total_quantity_kg,
        status="OPEN",
        departure_at=best.route.departure_at,
    )
    db.add(pool)
    db.flush()

    trip_kind = "return trip available" if best.route.return_available else "dedicated trip"
    reasoning = (
        f"{best.mandi.name} offers the highest expected net return after transport "
        f"and estimated spoilage ({best.price_per_kg:.0f}/kg vs "
        f"{baseline_price:.0f}/kg at {baseline_mandi.name}). Truck {best.truck.id} "
        f"({trip_kind}) carries {best.pool.total_quantity_kg:.0f}/"
        f"{best.truck.capacity_kg:.0f} kg for {len(best.pool.members)} farmers."
    )
    rec_row = Recommendation(
        reference=reference,
        farmer_listing_id=listing.id,
        baseline_mandi_id=baseline_mandi.id,
        recommended_mandi_id=best.mandi.id,
        truck_id=best.truck.id,
        pool_id=pool.id,
        baseline_profit=round(baseline_profit.net_profit),
        recommended_profit=round(best.profit.net_profit),
        transport_cost=round(best.profit.transport_cost),
        spoilage_loss=round(best.profit.spoilage_loss),
        net_gain=net_gain_value,
        score=best_score,
        reasoning=reasoning,
    )
    db.add(rec_row)
    db.commit()
    db.refresh(rec_row)

    farmer = db.get(Farmer, listing.farmer_id)
    facts = {
        "crop": crop.name,
        "quantity_kg": listing.quantity_kg,
        "village": farmer.village if farmer else "",
        "baseline_mandi": baseline_mandi.name,
        "baseline_price_per_kg": baseline_price,
        "recommended_mandi": best.mandi.name,
        "recommended_price_per_kg": best.price_per_kg,
        "truck": best.truck.id,
        "truck_registration": best.truck.registration_number,
        "is_return_trip": best.route.return_available,
        "pool_farmer_count": len(best.pool.members),
        "pool_total_kg": round(best.pool.total_quantity_kg),
        "truck_capacity_kg": best.truck.capacity_kg,
        "transport_share": round(best.profit.transport_cost),
        "net_gain": net_gain_value,
        "hours_remaining": round(best.spoilage_hours_remaining_at_departure, 1),
        "departure_time": best.route.departure_at.isoformat(timespec="minutes"),
        "data_is_seeded_demo": True,
    }
    explanation, llm_powered = llm_service.explain_recommendation(facts)
    if not any("seeded" in w.lower() for w in explanation.warnings):
        explanation.warnings.append("Mandi prices are seeded demo values.")

    arrival_risk = calculate_spoilage_risk(
        crop,
        listing.harvested_at,
        best.route.estimated_arrival_at,
        conditions.temperature_c,
        conditions.humidity_pct,
    )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "%s listing=%s candidates=%d valid=%d selected=%s gain=%.0f calc_ms=%d llm=%s",
        reference,
        listing_id,
        len(candidates),
        len(valid_candidates),
        best.candidate_id,
        net_gain_value,
        elapsed_ms,
        llm_powered,
    )

    map_points = {
        "farmer": {
            "name": farmer.village if farmer else "Farm",
            "latitude": listing.latitude,
            "longitude": listing.longitude,
        },
        "truck_origin": {
            "name": best.route.origin_name,
            "latitude": best.route.origin_latitude,
            "longitude": best.route.origin_longitude,
        },
        "recommended_mandi": {
            "name": best.mandi.name,
            "latitude": best.mandi.latitude,
            "longitude": best.mandi.longitude,
        },
        "alternative_mandis": [],
        "pool_members": [
            {
                "name": m.farmer.village,
                "latitude": m.listing.latitude,
                "longitude": m.listing.longitude,
            }
            for m in best.pool.members
            if m.distance_km > 0
        ],
    }

    alternatives = [
        _candidate_to_option(c, scores[c.candidate_id])
        for c in ranked[1 : 1 + MAX_ALTERNATIVES]
    ]

    return RecommendationResponse(
        recommendation_id=rec_row.reference,
        listing_id=listing.id,
        crop_name=crop.name,
        quantity_kg=listing.quantity_kg,
        pool_id=pool.id,
        baseline=_baseline_economics(
            baseline_mandi,
            baseline_price,
            baseline_transport.distance_km,
            baseline_profit,
        ),
        recommended=_candidate_to_option(best, best_score),
        alternatives=alternatives,
        net_gain=net_gain_value,
        spoilage=SpoilageInfo(
            risk_level=arrival_risk.risk_level,
            risk_score=arrival_risk.risk_score,
            hours_remaining=arrival_risk.hours_remaining,
            estimated_loss_percentage=arrival_risk.estimated_loss_percentage,
            temperature_c=conditions.temperature_c,
            humidity_pct=conditions.humidity_pct,
            crop_age_hours=round(crop_age_hours, 1),
        ),
        score=best_score,
        explanation=explanation,
        llm_powered=llm_powered,
        map_points=map_points,
        calculation_ms=elapsed_ms,
    )


def join_pool(
    db: Session, pool_id: int, listing_id: int, expected_net_gain: float | None = None
) -> JoinPoolResponse:
    """Join an OPEN pool: adds member, confirms pool, updates truck capacity."""
    pool = db.get(LoadPool, pool_id)
    if pool is None:
        raise LookupError(f"pool {pool_id} not found")
    listing = db.get(FarmerListing, listing_id)
    if listing is None:
        raise LookupError(f"listing {listing_id} not found")
    if pool.status not in ("OPEN", "CONFIRMED"):
        raise ValueError(f"pool {pool_id} is {pool.status} and cannot be joined")

    existing = db.execute(
        select(PoolMember).where(
            PoolMember.pool_id == pool_id,
            PoolMember.farmer_listing_id == listing_id,
        )
    ).scalar_one_or_none()

    if existing is None:
        members = db.execute(
            select(PoolMember).where(PoolMember.pool_id == pool_id)
        ).scalars().all()
        committed = sum(m.quantity_kg for m in members)
        share_denominator = max(pool.total_quantity_kg, committed + listing.quantity_kg)
        db.add(
            PoolMember(
                pool_id=pool_id,
                farmer_listing_id=listing_id,
                quantity_kg=listing.quantity_kg,
                transport_share=listing.quantity_kg / share_denominator,
                expected_profit=round(expected_net_gain or 0),
            )
        )

        truck = db.get(Truck, pool.truck_id)
        if truck is not None:
            truck.available_capacity_kg = max(
                0.0, truck.available_capacity_kg - listing.quantity_kg
            )

        pool.status = "CONFIRMED"
        listing.status = "POOLED"

    db.flush()
    mandi = db.get(Mandi, pool.destination_mandi_id)

    response = JoinPoolResponse(
        status="JOINED",
        message=(
            f"Your {listing.quantity_kg:.0f} kg has been added to the {pool.truck_id} "
            f"pooled load to {mandi.name}."
        ),
        pool_id=pool.id,
        truck_id=pool.truck_id,
        destination_mandi=mandi.name,
        departure_at=pool.departure_at,
        quantity_kg=listing.quantity_kg,
    )

    notify_pool_confirmed(db, listing, response)
    db.commit()
    return response
