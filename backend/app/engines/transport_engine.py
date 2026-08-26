"""Deterministic transport cost model.

MVP model:
    base_cost = fixed_cost + distance_km * cost_per_km

Return-trip loads get an explicit discount because the truck is already
travelling the corridor and would otherwise run empty.

When farmers pool, each farmer pays a share proportional to their load.
"""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class TransportBreakdown:
    distance_km: float
    base_cost: float
    return_trip: bool
    effective_total_cost: float
    total_pool_quantity_kg: float
    farmer_quantity_kg: float
    farmer_share: float
    utilization: float  # farmer share of pool quantity, 0-1


def calculate_transport_cost(
    distance_km: float,
    farmer_quantity_kg: float,
    total_pool_quantity_kg: float | None = None,
    return_trip: bool = False,
    fixed_cost: float | None = None,
    cost_per_km: float | None = None,
) -> TransportBreakdown:
    """Calculate the farmer's transport share for a leg.

    total_pool_quantity_kg defaults to the farmer's own quantity (solo trip).
    """
    if distance_km < 0:
        raise ValueError("distance_km cannot be negative")
    if farmer_quantity_kg <= 0:
        raise ValueError("farmer_quantity_kg must be positive")

    fixed = settings.TRANSPORT_FIXED_COST if fixed_cost is None else fixed_cost
    per_km = settings.TRANSPORT_COST_PER_KM if cost_per_km is None else cost_per_km

    pool_qty = (
        farmer_quantity_kg if total_pool_quantity_kg is None else total_pool_quantity_kg
    )
    if pool_qty <= 0:
        raise ValueError("total_pool_quantity_kg must be positive")
    if farmer_quantity_kg > pool_qty + 1e-9:
        raise ValueError("farmer quantity cannot exceed pool quantity")

    base_cost = fixed + distance_km * per_km
    effective_total = base_cost * (1 - settings.RETURN_TRIP_DISCOUNT) if return_trip else base_cost
    farmer_share = effective_total * farmer_quantity_kg / pool_qty

    return TransportBreakdown(
        distance_km=distance_km,
        base_cost=base_cost,
        return_trip=return_trip,
        effective_total_cost=effective_total,
        total_pool_quantity_kg=pool_qty,
        farmer_quantity_kg=farmer_quantity_kg,
        farmer_share=farmer_share,
        utilization=farmer_quantity_kg / pool_qty,
    )
