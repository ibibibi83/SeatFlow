"""
SeatFlow API – application entry point.

Starts the FastAPI application, registers all routers under /api/v1,
attaches a global exception handler, and manages the lifespan of the
database (via init_db) and the background scheduler.
"""


"""
SeatFlow API – application entry point.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.init_db import init_db

from app.routes.auth_router import router as auth_router
from app.routes.menu_router import router as menu_router
from app.routes.order_router import router as order_router
from app.routes.reservation_router import router as reservation_router
from app.routes.restaurant_router import router as seats_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("SeatFlow API starting up...")
    init_db()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("SeatFlow API shut down cleanly.")


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


API_PREFIX = "/api/v1"

app.include_router(auth_router,        prefix=API_PREFIX)
app.include_router(seats_router,       prefix=API_PREFIX)
app.include_router(reservation_router, prefix=API_PREFIX)
app.include_router(menu_router,        prefix=API_PREFIX)
app.include_router(order_router,       prefix=API_PREFIX)


@app.get("/health", tags=["System"], summary="Health check")
def health() -> dict:
    return {"status": "ok", "version": settings.APP_VERSION}


# ── Swagger Bearer Auth ───────────────────────────────────────────────────────
# Diese Routen brauchen KEINEN Token
PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/seats/availability",
    "/api/v1/menu",
    "/health",
}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path, methods in schema.get("paths", {}).items():
        for method in methods.values():
            if path in PUBLIC_PATHS:
                # Öffentliche Routen – kein Auth nötig
                method["security"] = []
            else:
                # Geschützte Routen – Bearer Token nötig
                method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# ── Frontend ──────────────────────────────────────────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")