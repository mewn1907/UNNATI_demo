"""Schemas for matching candidates and the recommendation object."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PoolMemberInfo(BaseModel):
    farmer_name: str
    village: str
    quantity_kg: float
    distance_km: float


class PoolInfo(BaseModel):
    farmer_count: int
    total_quantity_kg: float
    remaining_capacity_kg: float
    utilization_percent: float
    members: list[PoolMemberInfo] = []


class OptionEconomics(BaseModel):
    mandi_id: int | None = None
    mandi_name: str
    price_per_kg: float
    distance_km: float
    gross_revenue: float
    transport_cost: float
    spoilage_loss: float
    spoilage_percentage: float
    net_profit: float


class CandidateOption(OptionEconomics):
    candidate_id: str
    truck_id: str | None = None
    truck_registration: str | None = None
    is_return_trip: bool = False
    departure_at: datetime | None = None
    pool: PoolInfo | None = None
    score: float = 0.0
    valid: bool = True
    rejection_reason: str | None = None


class SpoilageInfo(BaseModel):
    risk_level: str
    risk_score: int
    hours_remaining: float
    estimated_loss_percentage: float
    temperature_c: float
    humidity_pct: float
    crop_age_hours: float
    disclaimer: str = "Estimated using crop age and environmental conditions. Actual spoilage may vary."


class LLMExplanation(BaseModel):
    headline: str
    summary: str
    why_this_option: list[str]
    action: str
    urgency: str
    warnings: list[str] = []


class RecommendationResponse(BaseModel):
    recommendation_id: str
    listing_id: int
    crop_name: str
    quantity_kg: float
    pool_id: int | None = None

    baseline: OptionEconomics
    recommended: CandidateOption
    alternatives: list[CandidateOption] = []

    net_gain: float
    spoilage: SpoilageInfo
    score: float
    explanation: LLMExplanation
    llm_powered: bool = False
    data_labels: dict[str, str] = Field(
        default_factory=lambda: {
            "prices": "Demo price · seeded prototype data",
            "weather": "Demo weather · used for prototype spoilage estimation",
        }
    )
    map_points: dict[str, Any] = Field(default_factory=dict)
    calculation_ms: int = 0


class JoinPoolRequest(BaseModel):
    listing_id: int


class JoinPoolResponse(BaseModel):
    status: str
    message: str
    pool_id: int
    truck_id: str
    destination_mandi: str
    departure_at: datetime
    quantity_kg: float
