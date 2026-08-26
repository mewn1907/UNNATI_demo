from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Truck(Base):
    __tablename__ = "trucks"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    registration_number: Mapped[str] = mapped_column(String(24))
    capacity_kg: Mapped[float] = mapped_column(Float)
    current_latitude: Mapped[float] = mapped_column(Float)
    current_longitude: Mapped[float] = mapped_column(Float)
    available_capacity_kg: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE")
