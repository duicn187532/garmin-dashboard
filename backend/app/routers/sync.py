from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from ..config import Settings, get_settings
from ..schemas import SyncRequest, SyncResponse
from ..services.garmin.base import GarminConnectorError
from ..services.garmin.unofficial import UnofficialGarminConnector
from ..store import MongoDataStore, SqlDataStore, get_store


router = APIRouter(prefix="/api/sync", tags=["sync"])

LAST_SYNC_STATUS: dict[str, Any] = {
    "state": "never_run",
    "message": "Sync has not run in this process.",
    "finished_at": None,
}


@router.post("/garmin", response_model=SyncResponse)
def sync_garmin(
    request: SyncRequest,
    store: SqlDataStore | MongoDataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
    x_sync_token: str | None = Header(default=None, alias="X-Sync-Token"),
    authorization: str | None = Header(default=None),
):
    require_sync_token(settings, x_sync_token, authorization)
    try:
        connector = build_garmin_connector(settings, store, request.mfa_code)
        response = store.sync(connector, days=request.days)
        LAST_SYNC_STATUS.update(
            {
                "state": "ok",
                "message": "Sync completed.",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "response": response.model_dump(),
            }
        )
        return response
    except GarminConnectorError as exc:
        LAST_SYNC_STATUS.update(
            {"state": "error", "message": str(exc), "finished_at": datetime.now(timezone.utc).isoformat()}
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/status")
def sync_status():
    return LAST_SYNC_STATUS


def require_sync_token(settings: Settings, x_sync_token: str | None, authorization: str | None) -> None:
    if not settings.sync_token:
        return
    bearer = f"Bearer {settings.sync_token}"
    if x_sync_token == settings.sync_token or authorization == bearer:
        return
    raise HTTPException(status_code=401, detail="Invalid sync token.")


def build_garmin_connector(
    settings: Settings,
    store: SqlDataStore | MongoDataStore,
    mfa_code: str | None = None,
) -> UnofficialGarminConnector:
    token_reader = getattr(store, "load_garmin_token_blob", None)
    token_writer = getattr(store, "save_garmin_token_blob", None)
    return UnofficialGarminConnector(
        settings,
        mfa_code=mfa_code,
        token_reader=token_reader if callable(token_reader) else None,
        token_writer=token_writer if callable(token_writer) else None,
    )
