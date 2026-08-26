"""Driver-facing read-only endpoints over the seeded demo network."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_listing import FarmerListing
from app.models.truck import Truck
from app.models.truck_route import TruckRoute
from app.services import driver_service
from app.services.chat_service import _location_index

router = APIRouter(prefix="/api/driver", tags=["driver"])


class OpportunitiesIn(BaseModel):
    origin_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity_kg: float = Field(gt=0, le=50_000)
    radius_km: float | None = Field(default=None, gt=0, le=300)


@router.post("/opportunities",
             summary="Ranked load bundles near the driver (deterministic, demo data)")
def opportunities(body: OpportunitiesIn, db: Session = Depends(get_db)) -> list[dict]:
    lat, lng = body.latitude, body.longitude
    if lat is None or lng is None:
        if not body.origin_name:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_INPUT",
                        "message": "Provide origin_name or latitude/longitude."},
            )
        entry = _location_index(db).get(body.origin_name.strip().lower())
        if entry is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND",
                        "message": f"Unknown origin '{body.origin_name}'."},
            )
        _, lat, lng = entry
    try:
        results = driver_service.find_opportunities(
            db, lat, lng, body.capacity_kg, body.radius_km
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc)}
        )
    return [
        {
            "crop": o.crop,
            "total_kg": o.total_kg,
            "load_count": o.load_count,
            "utilization_pct": o.utilization_pct,
            "best_option": {
                "mandi": o.best_option.mandi_name,
                "distance_km": o.best_option.distance_km,
                "price_per_kg": o.best_option.price_per_kg,
                "est_gross_inr": o.best_option.est_gross_inr,
            },
            "other_options": [
                {
                    "mandi": m.mandi_name,
                    "distance_km": m.distance_km,
                    "price_per_kg": m.price_per_kg,
                    "est_gross_inr": m.est_gross_inr,
                }
                for m in o.other_options
            ],
            "loads": [
                {
                    "listing_id": l.listing_id,
                    "farmer_name": l.farmer_name,
                    "village": l.village,
                    "crop": l.crop,
                    "quantity_kg": l.quantity_kg,
                    "distance_km": l.distance_km,
                }
                for l in o.loads
            ],
        }
        for o in results
    ]


@router.get("/dashboard", summary="Aggregate network stats for the driver dashboard (demo data)")
def dashboard(db: Session = Depends(get_db)) -> dict:
    listing_rows = db.execute(
        select(Crop.name, func.count(FarmerListing.id),
               func.coalesce(func.sum(FarmerListing.quantity_kg), 0.0))
        .join(Crop, FarmerListing.crop_id == Crop.id)
        .where(FarmerListing.status == "AVAILABLE")
        .group_by(Crop.name)
        .order_by(func.sum(FarmerListing.quantity_kg).desc())
    ).all()
    trucks = db.execute(select(Truck)).scalars().all()
    return_trips = db.execute(
        select(func.count(TruckRoute.id)).where(TruckRoute.return_available == True)  # noqa: E712
    ).scalar_one()

    total_kg = sum(r[2] for r in listing_rows)
    return {
        "label": "Demo network · seeded prototype data",
        "available_listings": sum(r[1] for r in listing_rows),
        "total_ready_kg": round(total_kg),
        "demand_by_crop": [
            {"crop": name, "listings": count, "quantity_kg": round(qty)}
            for name, count, qty in listing_rows
        ],
        "active_trucks": len(trucks),
        "return_trips": return_trips,
        "farmers_on_network": db.execute(
            select(func.count(Farmer.id.distinct()))
        ).scalar_one(),
    }
