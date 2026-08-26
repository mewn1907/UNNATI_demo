from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.weather_service import WeatherConditions, get_conditions

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("", summary="Current conditions used by the spoilage engine",
            description="Uses a live provider when configured; otherwise seeded demo "
                        "conditions so the demo never fails.")
def weather(latitude: float = 28.6139, longitude: float = 77.209,
            state: str = "", db: Session = Depends(get_db)) -> dict:
    conditions: WeatherConditions = get_conditions(latitude, longitude, state)
    return {
        "temperature_c": conditions.temperature_c,
        "humidity_pct": conditions.humidity_pct,
        "source": conditions.source,
        "label": conditions.label,
        "latitude": latitude,
        "longitude": longitude,
    }
