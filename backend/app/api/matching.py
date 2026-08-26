from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.farmer_listing import FarmerListing
from app.services.matching_service import find_compatible_listings, generate_candidates

router = APIRouter(prefix="/api/matching", tags=["matching"])


class CandidatesRequest(BaseModel):
    listing_id: int


def _candidate_summary(candidate) -> dict:
    return {
        "farmer_ids": [m.listing.farmer_id for m in candidate.pool.members],
        "truck_id": candidate.truck.id,
        "destination_mandi_id": candidate.mandi.id if candidate.mandi else None,
        "total_quantity_kg": candidate.pool.total_quantity_kg,
        "truck_capacity_kg": candidate.truck.capacity_kg,
        "remaining_capacity_kg": candidate.pool.remaining_capacity_kg,
        "price_per_kg": candidate.price_per_kg,
        "return_trip": candidate.route.return_available,
        "valid": candidate.valid,
        "rejection_reason": candidate.rejection_reason,
        "net_profit_for_target_farmer": round(candidate.profit.net_profit),
    }


@router.post("/candidates", summary="Raw matching candidates for a listing",
             description="Returns compatible farmer pools per truck route with hard "
                         "constraint results. Useful for transparency/debugging.")
def candidates(payload: CandidatesRequest, db: Session = Depends(get_db)) -> dict:
    listing = db.get(FarmerListing, payload.listing_id)
    if listing is None:
        raise HTTPException(status_code=404,
                            detail={"code": "NOT_FOUND", "message": "Listing not found."})

    now = datetime.now()
    compatible = find_compatible_listings(db, listing)
    candidate_list, _prices, _weather = generate_candidates(db, listing, now)

    return {
        "listing_id": listing.id,
        "compatible_farmers": [
            {
                "farmer_id": c.listing.farmer_id,
                "name": c.farmer.name,
                "village": c.farmer.village,
                "quantity_kg": c.listing.quantity_kg,
                "distance_km": c.distance_km,
            }
            for c in compatible
        ],
        "candidates": [_candidate_summary(c) for c in candidate_list],
    }
