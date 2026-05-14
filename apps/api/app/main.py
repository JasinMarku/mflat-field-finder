"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.cache import TTLCache
from app.clients.permits import PermitClient
from app.clients.socrata import SocrataClient
from app.config import get_settings
from app.routes import availability as availability_routes
from app.routes import facilities as facilities_routes
from app.routes import sports as sports_routes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    cache = TTLCache(settings.cache_db_path)
    app.state.settings = settings
    app.state.cache = cache
    app.state.socrata_client = SocrataClient(settings, cache)
    app.state.permit_client = PermitClient(settings, cache)
    yield


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
