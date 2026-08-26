from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.crop import Crop
from app.models.mandi import Mandi
from app.models.mandi_price import MandiPrice

router = APIRouter(prefix="/api/mandis", tags=["mandis"])


@router.get("", summary="All mandis")
def list_mandis(db: Session = Depends(get_db)) -> list[dict]:
    mandis = db.execute(select(Mandi).order_by(Mandi.name)).scalars().all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "city": m.city,
            "district": m.district,
            "state": m.state,
            "latitude": m.latitude,
            "longitude": m.longitude,
        }
        for m in mandis
    ]


@router.get("/prices", summary="Latest price per mandi for every crop (seeded demo data)")
def all_prices(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(MandiPrice, Mandi, Crop)
        .join(Mandi, MandiPrice.mandi_id == Mandi.id)
        .join(Crop, MandiPrice.crop_id == Crop.id)
        .order_by(MandiPrice.recorded_at)
    ).all()
    latest: dict[tuple[int, int], dict] = {}
    for price, mandi, crop in rows:
        latest[(mandi.id, crop.id)] = {
            "mandi_id": price.mandi_id,
            "mandi": mandi.name,
            "crop": crop.name,
            "price_per_kg": price.price_per_kg,
            "price_per_quintal": round(price.price_per_kg * 100),
            "recorded_at": price.recorded_at.isoformat(),
            "source": price.source,
            "label": "Demo price · seeded prototype data",
        }
    return list(latest.values())


@router.get("/prices/history",
            summary="Recent daily price history per mandi and crop (seeded demo data)")
def price_history(days: int = 7, db: Session = Depends(get_db)) -> list[dict]:
    days = max(1, min(days, 30))
    cutoff = datetime.now() - timedelta(days=days)
    rows = db.execute(
        select(MandiPrice, Mandi, Crop)
        .join(Mandi, MandiPrice.mandi_id == Mandi.id)
        .join(Crop, MandiPrice.crop_id == Crop.id)
        .where(MandiPrice.recorded_at >= cutoff)
        .order_by(MandiPrice.recorded_at)
    ).all()
    return [
        {
            "mandi_id": price.mandi_id,
            "mandi": mandi.name,
            "crop": crop.name,
            "price_per_kg": price.price_per_kg,
            "recorded_at": price.recorded_at.isoformat(),
            "label": "Demo price · seeded prototype data",
        }
        for price, mandi, crop in rows
    ]


@router.get("/{mandi_id}/prices", summary="Prices at one mandi")
def mandi_prices(mandi_id: int, db: Session = Depends(get_db)) -> list[dict]:
    if db.get(Mandi, mandi_id) is None:
        raise HTTPException(status_code=404,
                            detail={"code": "NOT_FOUND", "message": "Mandi not found."})
    rows = db.execute(
        select(MandiPrice, Crop).join(Crop, MandiPrice.crop_id == Crop.id)
        .where(MandiPrice.mandi_id == mandi_id)
        .order_by(MandiPrice.recorded_at)
    ).all()
    latest: dict[int, dict] = {}
    for price, crop in rows:
        latest[crop.id] = {
            "crop": crop.name,
            "price_per_kg": price.price_per_kg,
            "price_per_quintal": round(price.price_per_kg * 100),
            "recorded_at": price.recorded_at.isoformat(),
            "source": price.source,
            "label": "Demo price · seeded prototype data",
        }
    return list(latest.values())
