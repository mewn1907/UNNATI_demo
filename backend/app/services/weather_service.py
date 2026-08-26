"""Weather enrichment with seeded fallback.

The demo must not fail when the weather API is unavailable (specification 7).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("Unnati.weather")

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@dataclass(frozen=True)
class WeatherConditions:
    temperature_c: float
    humidity_pct: float
    source: str  # "open-meteo" | "seeded_demo"
    label: str


def _seeded_for_state(state: str) -> dict[str, Any]:
    try:
        payload = json.loads((DATA_DIR / "weather.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"temperature_c": 31.0, "humidity_pct": 62.0}
    regions: dict[str, Any] = payload.get("regions", {})
    return regions.get(state, regions.get("default", {"temperature_c": 31.0, "humidity_pct": 62.0}))


def _fetch_open_meteo(latitude: float, longitude: float) -> WeatherConditions | None:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m",
    }
    try:
        response = httpx.get(url, params=params, timeout=5.0)
        response.raise_for_status()
        current = response.json().get("current", {})
        temp = current.get("temperature_2m")
        hum = current.get("relative_humidity_2m")
        if temp is None or hum is None:
            return None
        return WeatherConditions(float(temp), float(hum), "open-meteo", "Live weather · open-meteo.com")
    except Exception as exc:  # noqa: BLE001 - weather must never break the demo
        logger.warning("Weather API unavailable (%s); using seeded conditions.", type(exc).__name__)
        return None


def get_conditions(latitude: float, longitude: float, state: str = "") -> WeatherConditions:
    if settings.WEATHER_ENABLED and settings.WEATHER_API_KEY:
        live = _fetch_open_meteo(latitude, longitude)
        if live is not None:
            return live
    seeded = _seeded_for_state(state or "")
    return WeatherConditions(
        temperature_c=float(seeded["temperature_c"]),
        humidity_pct=float(seeded["humidity_pct"]),
        source="seeded_demo",
        label="Demo weather · used for prototype spoilage estimation",
    )
