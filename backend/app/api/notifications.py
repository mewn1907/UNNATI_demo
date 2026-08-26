from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.notification import Notification
from app.services.notification_service import list_notifications

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/{farmer_id}", summary="Recent notifications for a farmer")
def notifications(farmer_id: int, db: Session = Depends(get_db)) -> list[dict]:
    rows: list[Notification] = list_notifications(db, farmer_id)
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]
