"""Deterministic profit calculation.

The LLM must never compute money. Everything in this module is pure Python.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfitBreakdown:
    quantity_kg: float
    price_per_kg: float
    spoilage_percentage: float  # 0-100
    sellable_quantity_kg: float
    gross_revenue: float
    spoilage_loss: float
    transport_cost: float
    net_profit: float


def calculate_profit(
    quantity_kg: float,
    price_per_kg: float,
    transport_cost: float,
    spoilage_percentage: float,
) -> ProfitBreakdown:
    """Compute expected economics for one sale option.

    spoilage_percentage: estimated share of the load (0-100) that will not be
    sellable by the time it reaches the mandi.
    """
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be positive")
    if price_per_kg < 0:
        raise ValueError("price_per_kg cannot be negative")
    if transport_cost < 0:
        raise ValueError("transport_cost cannot be negative")
    if not 0 <= spoilage_percentage <= 100:
        raise ValueError("spoilage_percentage must be within 0-100")

    spoilage_fraction = spoilage_percentage / 100.0
    sellable_quantity = quantity_kg * (1 - spoilage_fraction)
    expected_revenue = sellable_quantity * price_per_kg
    spoilage_loss = quantity_kg * spoilage_fraction * price_per_kg
    net_profit = expected_revenue - transport_cost

    return ProfitBreakdown(
        quantity_kg=quantity_kg,
        price_per_kg=price_per_kg,
        spoilage_percentage=spoilage_percentage,
        sellable_quantity_kg=sellable_quantity,
        gross_revenue=expected_revenue,
        spoilage_loss=spoilage_loss,
        transport_cost=transport_cost,
        net_profit=net_profit,
    )


def net_gain(recommended_net_profit: float, baseline_net_profit: float) -> float:
    return recommended_net_profit - baseline_net_profit
