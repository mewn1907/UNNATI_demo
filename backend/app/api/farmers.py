from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.crop import Crop

router = APIRouter(prefix="/api/farmers", tags=["farmers"])


class FarmerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = ""
    village: str = ""
    district: str = ""
    state: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


def _listing_payload(db: Session, farmer_id: int) -> list[dict]:
    rows = db.execute(
        select(FarmerListing, Crop)
        .join(Crop, FarmerListing.crop_id == Crop.id)
        .where(FarmerListing.farmer_id == farmer_id)
    ).all()
    return [
        {
            "id": listing.id,
            "crop": crop.name,
            "quantity_kg": listing.quantity_kg,
            "harvested_at": listing.harvested_at.isoformat(),
            "status": listing.status,
        }
        for listing, crop in rows
    ]


@router.post("", status_code=201, summary="Register a farmer")
def create_farmer(payload: FarmerCreate, db: Session = Depends(get_db)) -> dict:
    farmer = Farmer(**payload.model_dump())
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return {"id": farmer.id, "name": farmer.name, "village": farmer.village}


@router.get("", summary="All farmers with their listings (demo network view)")
def list_farmers(db: Session = Depends(get_db)) -> list[dict]:
    farmers = db.execute(select(Farmer).order_by(Farmer.id)).scalars().all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "village": f.village,
            "district": f.district,
            "state": f.state,
            "latitude": f.latitude,
            "longitude": f.longitude,
            "listings": _listing_payload(db, f.id),
        }
        for f in farmers
    ]


@router.get("/{farmer_id}", summary="Farmer details")
def get_farmer(farmer_id: int, db: Session = Depends(get_db)) -> dict:
    farmer = db.get(Farmer, farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Farmer not found."})
    return {
        "id": farmer.id,
        "name": farmer.name,
        "village": farmer.village,
        "district": farmer.district,
        "state": farmer.state,
        "latitude": farmer.latitude,
        "longitude": farmer.longitude,
        "listings": _listing_payload(db, farmer.id),
    }
