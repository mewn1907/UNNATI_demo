"""Deterministic candidate ranking.

Weights follow the specification:

    net_gain             40%
    pooling_benefit      20%
    truck_compatibility  15%
    spoilage_safety      15%
    route_efficiency     10%

Every component is normalised to 0-100 across the current candidate set so
scores are comparable. The highest-scoring VALID candidate wins.
"""

from dataclasses import dataclass

WEIGHTS = {
    "net_gain": 0.40,
    "pooling_benefit": 0.20,
    "truck_compatibility": 0.15,
    "spoilage_safety": 0.15,
    "route_efficiency": 0.10,
}

# Capacity utilisation considered ideal for pooling economics.
IDEAL_UTILIZATION = 0.85
RETURN_TRIP_BONUS = 15.0


@dataclass(frozen=True)
class CandidateMetrics:
    candidate_id: str
    # Absolute rupee advantage versus this farmer's own baseline option.
    net_gain: float
    # Rupees saved by sharing transport instead of hiring solo on same leg.
    pooling_benefit: float
    # Truck capacity utilisation of the pooled load (0-1) and return-trip flag.
    utilization: float
    is_return_trip: bool
    # Estimated hours left in the spoilage window at departure time.
    hours_remaining: float
    distance_km: float


def _component(values: list[float], invert: bool = False) -> list[float]:
    """Min-max normalise values to 0-100 (order-preserving)."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    spread = hi - lo
    if spread <= 1e-9:
        return [100.0] * len(values)
    scores = [(v - lo) / spread * 100.0 for v in values]
    if invert:
        scores = [100.0 - s for s in scores]
    return scores


def rank_candidates(metrics: list[CandidateMetrics]) -> dict[str, float]:
    """Return final 0-100 scores keyed by candidate_id."""
    gain_scores = _component([m.net_gain for m in metrics])
    pool_scores = _component([m.pooling_benefit for m in metrics])
    safety_scores = _component([min(m.hours_remaining, 72.0) for m in metrics])
    route_scores = _component([m.distance_km for m in metrics], invert=True)

    truck_scores = [
        max(0.0, min(100.0, 100.0 * (1.0 - abs(m.utilization - IDEAL_UTILIZATION) / IDEAL_UTILIZATION)))
        * 0.85
        + (RETURN_TRIP_BONUS if m.is_return_trip else 0.0)
        for m in metrics
    ]

    final: dict[str, float] = {}
    for i, m in enumerate(metrics):
        score = (
            WEIGHTS["net_gain"] * gain_scores[i]
            + WEIGHTS["pooling_benefit"] * pool_scores[i]
            + WEIGHTS["truck_compatibility"] * truck_scores[i]
            + WEIGHTS["spoilage_safety"] * safety_scores[i]
            + WEIGHTS["route_efficiency"] * route_scores[i]
        )
        final[m.candidate_id] = round(score, 2)
    return final
