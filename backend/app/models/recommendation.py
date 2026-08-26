from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(20), default="")
    farmer_listing_id: Mapped[int] = mapped_column(ForeignKey("farmer_listings.id"))
    baseline_mandi_id: Mapped[int | None] = mapped_column(
        ForeignKey("mandis.id"), nullable=True
    )
    recommended_mandi_id: Mapped[int | None] = mapped_column(
        ForeignKey("mandis.id"), nullable=True
    )
    truck_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pool_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_profit: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_profit: Mapped[float] = mapped_column(Float, default=0.0)
    transport_cost: Mapped[float] = mapped_column(Float, default=0.0)
    spoilage_loss: Mapped[float] = mapped_column(Float, default=0.0)
    net_gain: Mapped[float] = mapped_column(Float, default=0.0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
