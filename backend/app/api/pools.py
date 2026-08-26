from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.recommendation import JoinPoolRequest, JoinPoolResponse
from app.services.recommendation_service import join_pool

router = APIRouter(prefix="/api/pools", tags=["pools"])


@router.post("/{pool_id}/join", response_model=JoinPoolResponse,
             summary="Join a pooled load",
             description="Adds the farmer's listing to the pool, confirms the pool, "
                         "decrements truck capacity and creates a notification.")
def join(pool_id: int, payload: JoinPoolRequest,
         db: Session = Depends(get_db)) -> JoinPoolResponse:
    try:
        return join_pool(db, pool_id, payload.listing_id)
    except LookupError as exc:
        raise HTTPException(status_code=404,
                            detail={"code": "NOT_FOUND", "message": str(exc)}) from None
    except ValueError as exc:
        raise HTTPException(status_code=409,
                            detail={"code": "INVALID_INPUT", "message": str(exc)}) from None
