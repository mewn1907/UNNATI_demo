from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crop import Crop
from app.models.farmer_listing import FarmerListing
from app.schemas.listing import ListingCreate, ListingRead
from app.utils.time import ensure_utc_naive

router = APIRouter(prefix="/api/listings", tags=["listings"])


def _find_crop(db: Session, name: str) -> Crop | None:
    lowered = name.strip().lower()
    for candidate in db.execute(select(Crop)).scalars().all():
        if candidate.name.lower() == lowered:
            return candidate
    return None


@router.post("", response_model=ListingRead, status_code=201,
             summary="Create a produce listing",
             description="Primary farmer input flow. The backend determines prices, "
                         "transport and spoilage — the farmer never enters those.")
def create_listing(payload: ListingCreate, db: Session = Depends(get_db)) -> ListingRead:
    crop = _find_crop(db, payload.crop)
    if crop is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"Unknown crop '{payload.crop}'."},
        )

    harvested_at = payload.parsed_harvested_at()
    if harvested_at is None:
        harvested_at = datetime.now() - timedelta(hours=2)
    else:
        harvested_at = ensure_utc_naive(harvested_at)

    listing = FarmerListing(
        farmer_id=1,  # demo default farmer; authentication is out of MVP scope
        crop_id=crop.id,
        quantity_kg=payload.quantity_kg,
        harvested_at=harvested_at,
        available_until=harvested_at + timedelta(days=3),
        latitude=payload.latitude,
        longitude=payload.longitude,
        status="AVAILABLE",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/{listing_id}", response_model=ListingRead, summary="Listing details")
def get_listing(listing_id: int, db: Session = Depends(get_db)) -> ListingRead:
    listing = db.get(FarmerListing, listing_id)
    if listing is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Listing not found."},
        )
    return listing
