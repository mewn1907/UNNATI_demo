from datetime import datetime

from app.services.matching_service import (
    find_compatible_listings,
    generate_candidates,
)


def test_golden_listing_finds_nearby_tomato_farmers(db_session):
    listing = _get_listing(db_session, 1)
    compatible = find_compatible_listings(db_session, listing)
    names = {c.farmer.name for c in compatible}
    assert "Suresh Yadav" in names and "Amit Chauhan" in names
    # Different crop / far / sold listings must be excluded.
    assert all(c.listing.crop_id == listing.crop_id for c in compatible)


def test_candidates_generated_and_constrained(db_session):
    listing = _get_listing(db_session, 1)
    candidates, prices, weather = generate_candidates(
        db_session, listing, datetime.now()
    )
    assert len(candidates) > 0
    assert prices  # tomato has seeded prices everywhere
    assert weather.temperature_c > 0
    # Every valid candidate respects capacity.
    for candidate in candidates:
        if candidate.valid:
            assert candidate.pool.total_quantity_kg <= candidate.truck.available_capacity_kg + 1e-6
    # Golden truck T104 with return trip must appear among candidates.
    t104 = [c for c in candidates if c.truck.id == "T104"]
    assert t104 and t104[0].route.return_available


def _get_listing(db_session, listing_id: int):
    from app.models.farmer_listing import FarmerListing

    listing = db_session.get(FarmerListing, listing_id)
    assert listing is not None
    return listing
