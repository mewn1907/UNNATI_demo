"""Unnati FastAPI application entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import (
    chat,
    crops,
    demo,
    farmers,
    health,
    listings,
    mandis,
    matching,
    notifications,
    pools,
    recommendations,
    trucks,
    weather,
)
from app.core.config import settings
from app.db.base import create_all
from app.db.seed import seed

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("Unnati")

app = FastAPI(
    title="Unnati API",
    version="1.0.0",
    description=(
        "AI-powered agricultural logistics copilot. Deterministic engines compute "
        "pooling, transport, spoilage and profit; the LLM only explains results.\n\n"
        "**Demo notice:** mandi prices and weather are seeded demo data."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_all()
    if settings.DEMO_MODE:
        seed()
        logger.info("Demo mode: database seeded with the golden scenario.")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalise errors to {error:{code,message}} without stack traces."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        payload = {"error": detail}
    else:
        payload = {"error": {"code": "INVALID_INPUT", "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {
            "code": "INTERNAL_ERROR",
            "message": "Something went wrong. Please try again in a moment.",
        }},
    )


for router in (
    health.router,
    crops.router,
    farmers.router,
    listings.router,
    trucks.router,
    mandis.router,
    matching.router,
    recommendations.router,
    pools.router,
    weather.router,
    notifications.router,
    demo.router,
    chat.router,
):
    app.include_router(router)

# Serve the built React frontend (single-service deployment, e.g. Render).
_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST_DIR.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=_DIST_DIR / "assets"),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        """Client-side routing: unknown paths return index.html."""
        candidate = _DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST_DIR / "index.html")
