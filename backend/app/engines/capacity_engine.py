"""Hard capacity validation. The LLM can never override this."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CapacityResult:
    fits: bool
    reason: str
    total_quantity_kg: float
    available_capacity_kg: float
    remaining_capacity_kg: float


def check_capacity(total_quantity_kg: float, available_capacity_kg: float) -> CapacityResult:
    if available_capacity_kg < 0:
        raise ValueError("available_capacity_kg cannot be negative")
    remaining = available_capacity_kg - total_quantity_kg
    if total_quantity_kg <= 0:
        return CapacityResult(False, "quantity must be positive", total_quantity_kg, available_capacity_kg, remaining)
    if remaining >= -1e-9:
        return CapacityResult(
            True,
            "load fits within available truck capacity",
            total_quantity_kg,
            available_capacity_kg,
            max(0.0, remaining),
        )
    return CapacityResult(
        False,
        f"combined load {total_quantity_kg:.0f} kg exceeds available capacity "
        f"{available_capacity_kg:.0f} kg",
        total_quantity_kg,
        available_capacity_kg,
        remaining,
    )


def utilization_percent(total_quantity_kg: float, capacity_kg: float) -> float:
    if capacity_kg <= 0:
        raise ValueError("capacity_kg must be positive")
    return min(100.0, total_quantity_kg / capacity_kg * 100.0)
