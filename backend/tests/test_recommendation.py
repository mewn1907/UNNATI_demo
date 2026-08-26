from datetime import datetime

import pytest

from app.services.recommendation_service import (
    NoValidMatchError,
    get_recommendation,
)


def test_golden_recommendation_targets_spec_narrative(db_session):
    rec = get_recommendation(db_session, listing_id=1)

    # Golden truck + pooled load + return trip.
    assert rec.recommended.truck_id == "T104"
    assert rec.recommended.is_return_trip is True
    assert rec.recommended.pool.farmer_count == 3
    assert rec.recommended.pool.total_quantity_kg == 2100

    # Deterministic economics in the spec's target band (~₹12k gain).
    assert rec.baseline.mandi_name == "Azadpur Mandi"
    assert rec.net_gain > 8000
    assert rec.recommended.net_profit > rec.baseline.net_profit

    # Ranking picked the best valid candidate.
    assert rec.score > 50
    assert rec.explanation.summary  # fallback or LLM text present
    assert any("seeded" in w.lower() for w in rec.explanation.warnings)


def test_alternatives_are_valid_and_ranked_below_best(db_session):
    rec = get_recommendation(db_session, listing_id=1)
    for alt in rec.alternatives:
        assert alt.net_profit <= rec.recommended.net_profit + 1e-6
        assert alt.valid is True


def test_missing_listing_raises_lookup(db_session):
    with pytest.raises(LookupError):
        get_recommendation(db_session, listing_id=99999)


def test_expired_produce_has_no_match(db_session):
    """Produce harvested far beyond its shelf life must yield no valid option."""
    from datetime import timedelta

    from app.models.crop import Crop
    from app.models.farmer_listing import FarmerListing

    crop = db_session.query(Crop).filter(Crop.name == "Tomato").one()
    rotten = FarmerListing(
        farmer_id=1,
        crop_id=crop.id,
        quantity_kg=500,
        harvested_at=datetime.now() - timedelta(days=10),
        available_until=datetime.now() + timedelta(days=1),
        latitude=28.683,
        longitude=77.06,
        status="AVAILABLE",
    )
    db_session.add(rotten)
    db_session.commit()
    db_session.refresh(rotten)

    with pytest.raises(NoValidMatchError):
        get_recommendation(db_session, listing_id=rotten.id)

    # Restore state for later tests (session-scoped DB).
    db_session.delete(rotten)
    db_session.commit()
