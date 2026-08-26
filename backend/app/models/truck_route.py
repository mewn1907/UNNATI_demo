from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TruckRoute(Base):
    __tablename__ = "truck_routes"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    truck_id: Mapped[str] = mapped_column(ForeignKey("trucks.id"))
    origin_name: Mapped[str] = mapped_column(String(120))
    origin_latitude: Mapped[float] = mapped_column(Float)
    origin_longitude: Mapped[float] = mapped_column(Float)
    destination_mandi_id: Mapped[int | None] = mapped_column(
        ForeignKey("mandis.id"), nullable=True
    )
    departure_at: Mapped[datetime] = mapped_column(DateTime)
    estimated_arrival_at: Mapped[datetime] = mapped_column(DateTime)
    # True when this leg is a return trip that would otherwise run empty.
    return_available: Mapped[bool] = mapped_column(default=False)
    return_origin_mandi_id: Mapped[int | None] = mapped_column(
        ForeignKey("mandis.id"), nullable=True
    )
    return_destination_region: Mapped[str] = mapped_column(String(120), default="")
    distance_km: Mapped[float] = mapped_column(Float)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
