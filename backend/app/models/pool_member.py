from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PoolMember(Base):
    __tablename__ = "pool_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("load_pools.id"))
    farmer_listing_id: Mapped[int] = mapped_column(ForeignKey("farmer_listings.id"))
    quantity_kg: Mapped[float] = mapped_column(Float)
    transport_share: Mapped[float] = mapped_column(Float, default=0.0)
    expected_profit: Mapped[float] = mapped_column(Float, default=0.0)
