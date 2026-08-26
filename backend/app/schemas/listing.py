from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.utils.time import parse_datetime


class ListingCreate(BaseModel):
    """Primary farmer input flow (specification section 10)."""

    crop: str = Field(min_length=1, max_length=80)
    quantity_kg: float = Field(gt=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    harvested_at: str | None = None
    preferred_radius_km: float | None = Field(default=None, gt=0, le=300)
    language: str = "en"

    def parsed_harvested_at(self) -> datetime | None:
        return parse_datetime(self.harvested_at)


class ListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farmer_id: int
    crop_id: int
    quantity_kg: float
    harvested_at: datetime
    latitude: float
    longitude: float
    status: str
