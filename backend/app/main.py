from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import activities, ai, dashboard, health, status, sync
from .store import MongoDataStore


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_backend == "mongodb":
        try:
            MongoDataStore(settings).ensure_indexes()
        except Exception as exc:
            logger.warning("MongoDB index initialization failed: %s", exc)
    else:
        init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def app_access_auth(request: Request, call_next):
    if should_require_app_token(request):
        token = request.headers.get("X-App-Token")
        authorization = request.headers.get("Authorization")
        sync_token = request.headers.get("X-Sync-Token")
        if token != settings.app_access_token and authorization != f"Bearer {settings.app_access_token}":
            if not (request.url.path.startswith("/api/sync") and sync_token == settings.sync_token):
                return JSONResponse({"detail": "Invalid app access token."}, status_code=401)
    return await call_next(request)


def should_require_app_token(request: Request) -> bool:
    if not settings.app_access_token:
        return False
    if not request.url.path.startswith("/api"):
        return False
    return request.url.path not in {"/api/status"}


app.include_router(status.router)
app.include_router(sync.router)
app.include_router(dashboard.router)
app.include_router(activities.router)
app.include_router(health.router)
app.include_router(ai.router)
