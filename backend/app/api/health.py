from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health", summary="Service health check")
def health() -> dict:
    return {"status": "ok", "service": "Unnati-api", "time": datetime.now().isoformat(timespec="seconds")}
