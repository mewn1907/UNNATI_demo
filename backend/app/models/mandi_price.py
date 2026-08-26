from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MandiPrice(Base):
    __tablename__ = "mandi_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mandi_id: Mapped[int] = mapped_column(ForeignKey("mandis.id"))
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id"))
    price_per_kg: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    source: Mapped[str] = mapped_column(String(40), default="seeded_demo")
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
