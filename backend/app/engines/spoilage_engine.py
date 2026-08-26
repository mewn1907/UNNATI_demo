"""Spoilage-risk estimation.

This is an explicit ESTIMATE for prioritisation, never a guarantee. The model
combines crop shelf life, harvest age, temperature and humidity into:

    risk_level        LOW | MEDIUM | HIGH | CRITICAL
    risk_score        0-100
    hours_remaining   estimated window before the risk window closes
    loss_percentage   estimated share of the load that will not sell
"""

from dataclasses import dataclass
from datetime import datetime

from app.models.crop import Crop
from app.utils.time import clamp, hours_between

# Ambient reference conditions used by the crop shelf-life baselines.
REFERENCE_TEMP_C = 25.0
REFERENCE_HUMIDITY_PCT = 60.0

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


@dataclass(frozen=True)
class SpoilageRisk:
    risk_level: str
    risk_score: int  # 0-100
    hours_remaining: float
    estimated_loss_percentage: float


def _aging_factor(temperature_c: float, humidity_pct: float, crop: Crop) -> float:
    """How much faster than baseline the crop ages under given conditions."""
    temp_component = max(0.0, temperature_c - REFERENCE_TEMP_C) * crop.temperature_sensitivity
    # Very high humidity accelerates decay modestly; very dry air dries leafy produce.
    humidity_delta = (humidity_pct - REFERENCE_HUMIDITY_PCT) / 100.0
    humidity_component = 0.15 * humidity_delta
    factor = 1.0 + temp_component + humidity_component
    return clamp(factor, 0.5, 4.0)


def calculate_spoilage_risk(
    crop: Crop,
    harvested_at: datetime,
    current_time: datetime,
    temperature_c: float = 30.0,
    humidity_pct: float = 65.0,
) -> SpoilageRisk:
    age_hours = max(0.0, hours_between(harvested_at, current_time))

    factor = _aging_factor(temperature_c, humidity_pct, crop)
    effective_age = age_hours * factor

    shelf_life = max(1.0, crop.baseline_shelf_life_hours)
    life_used = clamp(effective_age / shelf_life, 0.0, 1.6)

    remaining_fraction = clamp(1.0 - effective_age / shelf_life, 0.0, 1.0)
    hours_remaining = remaining_fraction * shelf_life / factor

    # Loss ramps up once half of the usable life is gone.
    loss_pct = clamp((life_used - 0.5) * 40.0, 0.0, 60.0)

    score = int(round(clamp(life_used * 100.0, 0.0, 100.0)))
    if score < 25:
        level = "LOW"
    elif score < 50:
        level = "MEDIUM"
    elif score < 75:
        level = "HIGH"
    else:
        level = "CRITICAL"

    return SpoilageRisk(
        risk_level=level,
        risk_score=score,
        hours_remaining=round(hours_remaining, 2),
        estimated_loss_percentage=round(loss_pct, 1),
    )
