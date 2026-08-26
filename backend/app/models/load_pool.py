from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoadPool(Base):
    __tablename__ = "load_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    truck_id: Mapped[str] = mapped_column(ForeignKey("trucks.id"))
    destination_mandi_id: Mapped[int] = mapped_column(ForeignKey("mandis.id"))
    total_quantity_kg: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    departure_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
