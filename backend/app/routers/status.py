from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..config import Settings, get_settings
from ..store import MongoDataStore, SqlDataStore, get_store


router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
def status(
    store: SqlDataStore | MongoDataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    store.ping()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "database_backend": settings.database_backend,
        "time": datetime.now(timezone.utc).isoformat(),
    }

