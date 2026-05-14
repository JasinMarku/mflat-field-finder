"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.cache import TTLCache
from app.clients.permits import PermitClient
from app.clients.socrata import SocrataClient
from app.config import get_settings
from app.models import Sport
from app.routes import availability as availability_routes
from app.routes import facilities as facilities_routes
from app.routes import sports as sports_routes


logger = logging.getLogger(__name__)


_POPULAR_SPORTS: tuple[Sport, ...] = (
    Sport.SOCCER,
    Sport.BASEBALL,
    Sport.SOFTBALL,
    Sport.BASKETBALL,
    Sport.TENNIS,
    Sport.HANDBALL,
)


async def prefetch_popular_sports(
    socrata: SocrataClient,
    permits: PermitClient,
) -> None:
    try:
        facilities = await socrata.get_all_facilities()
        unique_parks: set[str] = set()
        for facility in facilities:
            if any(s in facility.sports for s in _POPULAR_SPORTS):
                unique_parks.add(facility.park_id)
        logger.info(
            "Prefetching permits for %d parks in background...",
            len(unique_parks),
        )
        t0 = time.monotonic()
        await permits.get_permits_for_parks(sorted(unique_parks))
        logger.info(
            "Permit prefetch complete in %.1fs",
            time.monotonic() - t0,
        )
    except Exception as exc:
        logger.warning("Background prefetch failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    cache = TTLCache(settings.cache_db_path)
    socrata = SocrataClient(settings, cache)
    permit_client = PermitClient(settings, cache)

    app.state.settings = settings
    app.state.cache = cache
    app.state.socrata_client = socrata
    app.state.permit_client = permit_client

    facilities = await socrata.get_all_facilities()
    logger.info("Catalog warmed: %d facilities.", len(facilities))

    prefetch_task = asyncio.create_task(prefetch_popular_sports(socrata, permit_client))
    app.state.prefetch_task = prefetch_task

    try:
        yield
    finally:
        if not prefetch_task.done():
            prefetch_task.cancel()


app = FastAPI(
    title="Field Finder API",
    version=__version__,
    description="NYC Parks athletic field availability search.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(sports_routes.router)
app.include_router(facilities_routes.router)
app.include_router(availability_routes.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


_static_dir = os.getenv("STATIC_DIR")
if _static_dir and Path(_static_dir).exists():
    _static_path = Path(_static_dir)
    _assets_path = _static_path / "assets"
    if _assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_path)), name="assets")

    _index_path = _static_path / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> Response:
        if full_path.startswith(("api/", "health", "docs", "openapi", "redoc")):
            return Response(status_code=404)
        return FileResponse(_index_path)
