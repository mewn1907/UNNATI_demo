from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FarmerListing(Base):
    __tablename__ = "farmer_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"))
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"))
    quantity_kg: Mapped[float] = mapped_column(Float)
    harvested_at: Mapped[datetime] = mapped_column(DateTime)
    available_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
