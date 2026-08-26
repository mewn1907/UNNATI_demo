from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.mandi import Mandi
from app.models.truck import Truck
from app.models.truck_route import TruckRoute

router = APIRouter(prefix="/api/trucks", tags=["trucks"])


@router.get("", summary="All trucks with current routes")
def list_trucks(db: Session = Depends(get_db)) -> list[dict]:
    trucks = db.execute(select(Truck).order_by(Truck.id)).scalars().all()
    routes_by_truck: dict[str, list[TruckRoute]] = {}
    for route in db.execute(select(TruckRoute)).scalars().all():
        routes_by_truck.setdefault(route.truck_id, []).append(route)

    mandis = {m.id: m.name for m in db.execute(select(Mandi)).scalars().all()}

    result = []
    for t in trucks:
        routes = []
        for r in routes_by_truck.get(t.id, []):
            routes.append(
                {
                    "route_id": r.id,
                    "origin_name": r.origin_name,
                    "origin_latitude": r.origin_latitude,
                    "origin_longitude": r.origin_longitude,
                    "destination_mandi_id": r.destination_mandi_id,
                    "destination_mandi": mandis.get(r.destination_mandi_id or -1),
                    "departure_at": r.departure_at.isoformat(),
                    "estimated_arrival_at": r.estimated_arrival_at.isoformat(),
                    "return_available": r.return_available,
                    "return_destination_region": r.return_destination_region,
                    "distance_km": r.distance_km,
                }
            )
        result.append(
            {
                "id": t.id,
                "registration_number": t.registration_number,
                "capacity_kg": t.capacity_kg,
                "available_capacity_kg": t.available_capacity_kg,
                "status": t.status,
                "current_latitude": t.current_latitude,
                "current_longitude": t.current_longitude,
                "routes": routes,
            }
        )
    return result


@router.get("/{truck_id}", summary="Truck details")
def get_truck(truck_id: str, db: Session = Depends(get_db)) -> dict:
    truck = db.get(Truck, truck_id)
    if truck is None:
        raise HTTPException(status_code=404,
                            detail={"code": "NOT_FOUND", "message": "Truck not found."})
    return next((t for t in list_trucks(db) if t["id"] == truck.id), {})
