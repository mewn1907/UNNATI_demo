"""Demo-mode helpers: reset & reseed, golden scenario shortcut."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.seed import seed

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/reset", summary="Reset and reseed the demo dataset",
             description="Only available when DEMO_MODE=true. Recreates all seeded "
                         "data with departure times relative to now so the demo is "
                         "always fresh.")
def reset(db: Session = Depends(get_db)) -> dict:
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403,
                            detail={"code": "FORBIDDEN",
                                    "message": "Demo mode is disabled."})
    seed()
    return {"status": "reseeded", "demo_mode": True}
