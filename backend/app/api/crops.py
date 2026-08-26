from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crop import Crop

router = APIRouter(prefix="/api/crops", tags=["crops"])


@router.get("", summary="Supported crops with shelf-life parameters")
def list_crops(db: Session = Depends(get_db)) -> list[dict]:
    crops = db.execute(select(Crop).order_by(Crop.name)).scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "category": c.category,
            "unit": c.unit,
            "baseline_shelf_life_hours": c.baseline_shelf_life_hours,
        }
        for c in crops
    ]
