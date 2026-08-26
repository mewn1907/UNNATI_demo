"""Notification creation and retrieval.

The current provider is the in-app WebNotificationProvider. The interface is
deliberately simple so it can later be swapped for a WhatsAppProvider.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.farmer_listing import FarmerListing
from app.models.notification import Notification
from app.schemas.recommendation import JoinPoolResponse


def create_notification(
    db: Session,
    farmer_id: int,
    type_: str,
    title: str,
    message: str,
    send_now: bool = True,
) -> Notification:
    notification = Notification(
        farmer_id=farmer_id,
        type=type_,
        title=title[:200],
        message=message[:500],
        sent_at=datetime.now() if send_now else None,
        status="SENT" if send_now else "PENDING",
    )
    db.add(notification)
    db.flush()
    return notification


def notify_pool_confirmed(
    db: Session, listing: FarmerListing, join_result: JoinPoolResponse
) -> None:
    departure_label = join_result.departure_at.strftime("%d %b · %I:%M %p")
    create_notification(
        db,
        listing.farmer_id,
        "POOL_CONFIRMED",
        "Load confirmed.",
        (
            f"{join_result.message} Departure: {departure_label}. "
            f"Destination: {join_result.destination_mandi}."
        ),
    )


def notify_truck_departing(db: Session, farmer_id: int, truck_id: str, hours: float) -> None:
    create_notification(
        db,
        farmer_id,
        "TRUCK_DEPARTURE",
        f"Truck {truck_id} departs soon.",
        f"Truck {truck_id} departs in {hours:.0f} hours. Be ready at the pickup point.",
        send_now=False,
    )


def list_notifications(db: Session, farmer_id: int) -> list[Notification]:
    return list(
        db.execute(
            select(Notification)
            .where(Notification.farmer_id == farmer_id)
            .order_by(Notification.created_at.desc())
            .limit(30)
        ).scalars().all()
    )
