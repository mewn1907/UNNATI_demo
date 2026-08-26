from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    category: Mapped[str] = mapped_column(String(40), default="vegetable")
    unit: Mapped[str] = mapped_column(String(16), default="kg")
    # Baseline shelf life in hours at ~20C ambient storage.
    baseline_shelf_life_hours: Mapped[float] = mapped_column(Float, default=72.0)
    # Multiplier applied to aging speed per degree C above 25C.
    temperature_sensitivity: Mapped[float] = mapped_column(Float, default=0.06)
