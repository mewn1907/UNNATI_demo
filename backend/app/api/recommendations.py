from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import NoValidMatchError, get_recommendation

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class RecommendationRequest(BaseModel):
    listing_id: int = Field(gt=0)


@router.post("", response_model=RecommendationResponse,
             summary="Compute the best logistics + market option for a listing",
             description="Runs the full deterministic pipeline: farmer pooling, truck "
                         "matching (preferring empty-return trips), mandi comparison, "
                         "transport/spoilage/profit calculation and ranking. An LLM "
                         "explains the result but never computes it.")
def create_recommendation(payload: RecommendationRequest,
                          db: Session = Depends(get_db)) -> RecommendationResponse:
    try:
        return get_recommendation(db, payload.listing_id)
    except LookupError:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND",
            "message": "Listing not found. Create the listing first.",
        }) from None
    except NoValidMatchError as exc:
        raise HTTPException(status_code=404, detail={
            "code": "NO_VALID_MATCH",
            "message": str(exc),
            "suggestions": [
                "Increase your pickup radius",
                "Try another departure time",
                "View other mandis",
            ],
        }) from None
    except Exception:  # noqa: BLE001 - never leak stack traces to users
        raise HTTPException(status_code=500, detail={
            "code": "INTERNAL_ERROR",
            "message": "Something went wrong while calculating your recommendation.",
        }) from None


@router.get("/latest/{listing_id}", response_model=RecommendationResponse,
            summary="Most recent recommendation for a listing")
def latest_recommendation(listing_id: int, db: Session = Depends(get_db)) -> RecommendationResponse:
    from app.models.recommendation import Recommendation

    row = db.execute(
        select(Recommendation).where(Recommendation.farmer_listing_id == listing_id)
        .order_by(Recommendation.id.desc()).limit(1)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND",
            "message": "No recommendation exists for this listing yet.",
        })
    return get_recommendation(db, listing_id)
