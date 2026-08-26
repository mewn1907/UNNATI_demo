from datetime import datetime, timedelta

import pytest

from app.engines.spoilage_engine import calculate_spoilage_risk
from app.models.crop import Crop

TOMATO = Crop(
    id=1,
    name="Tomato",
    category="vegetable",
    unit="kg",
    baseline_shelf_life_hours=40,
    temperature_sensitivity=0.06,
)
WHEAT = Crop(
    id=9,
    name="Wheat",
    category="grain",
    unit="kg",
    baseline_shelf_life_hours=8760,
    temperature_sensitivity=0.002,
)


def test_fresh_produce_low_risk():
    now = datetime.now()
    risk = calculate_spoilage_risk(TOMATO, now - timedelta(hours=1), now, 28, 60)
    assert risk.risk_level in ("LOW", "MEDIUM")
    assert risk.hours_remaining > 24
    assert risk.estimated_loss_percentage == 0


def test_old_produce_high_risk():
    now = datetime.now()
    risk = calculate_spoilage_risk(TOMATO, now - timedelta(hours=30), now, 31, 62)
    # effective age ~30*1.37=41h > 40h shelf life -> critical/very high
    assert risk.risk_level in ("HIGH", "CRITICAL")
    assert risk.hours_remaining < 6
    assert risk.estimated_loss_percentage > 5


def test_hot_weather_ages_faster():
    now = datetime.now()
    harvested = now - timedelta(hours=10)
    cool = calculate_spoilage_risk(TOMATO, harvested, now, 20, 50)
    hot = calculate_spoilage_risk(TOMATO, harvested, now, 38, 70)
    assert hot.risk_score > cool.risk_score
    assert hot.hours_remaining < cool.hours_remaining


def test_cool_weather_slows_aging():
    now = datetime.now()
    harvested = now - timedelta(hours=10)
    cool = calculate_spoilage_risk(TOMATO, harvested, now, 15, 40)
    assert cool.risk_score <= 30


def test_durable_crop_stays_low():
    now = datetime.now()
    risk = calculate_spoilage_risk(WHEAT, now - timedelta(days=30), now, 35, 40)
    assert risk.risk_level == "LOW"


def test_future_harvest_clamped_not_crash():
    now = datetime.now()
    risk = calculate_spoilage_risk(TOMATO, now + timedelta(days=2), now, 30, 60)
    assert risk.risk_level == "LOW"
