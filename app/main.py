"""
SeatFlow API – application entry point.

Starts the FastAPI application, registers all routers under /api/v1,
attaches a global exception handler, and manages the lifespan of the
database (via init_db) and the background scheduler.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.init_db import init_db

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routes.auth_router import router as auth_router
from app.routes.menu_router import router as menu_router
from app.routes.order_router import router as order_router
from app.routes.reservation_routes import router as reservation_router
from app.routes.restauran_router import router as seats_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan hook.

    Code before 'yield' runs on startup; code after 'yield' runs on shutdown.
    - init_db  : creates tables and inserts seed data if the database is empty.
    - scheduler: runs the reservation-expiry sweep every 60 seconds.
    """
    logger.info("SeatFlow API starting up...")
    init_db()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("SeatFlow API shut down cleanly.")


# ── Application instance ──────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Restaurant reservation and order management system for Blockbräu Hamburg.\n\n"
        "**Public endpoints** require no authentication.\n"
        "**Management endpoints** require a Bearer token with a staff role.\n\n"
        "Default credentials:\n"
        "- `ops_manager` / `ops123`\n"
        "- `shift_manager` / `shift123`"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Convert any AppException (and its subclasses) to a consistent JSON error response.
    This means route handlers never need to manually raise HTTPException.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

# ── Routers ───────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(auth_router,        prefix=API_PREFIX)   # /api/v1/auth/...
app.include_router(seats_router,       prefix=API_PREFIX)   # /api/v1/seats/...
app.include_router(reservation_router, prefix=API_PREFIX)   # /api/v1/reservations/...
app.include_router(menu_router,        prefix=API_PREFIX)   # /api/v1/menu/...
app.include_router(order_router,       prefix=API_PREFIX)   # /api/v1/orders/...

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check")
def health() -> dict:
    """Returns HTTP 200 if the server is running. Used by load balancers."""
    return {"status": "ok", "version": settings.APP_VERSION}