from dataclasses import replace

from fastapi.testclient import TestClient

import app.main as main


def test_app_access_token_protects_private_api(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, app_access_token="test-token"))
    with TestClient(main.app) as client:
        denied = client.get("/api/summary")
        allowed = client.get("/api/summary", headers={"X-App-Token": "test-token"})
    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_app_access_token_allows_cors_preflight(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, app_access_token="test-token"))
    with TestClient(main.app) as client:
        response = client.options(
            "/api/summary",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-App-Token",
            },
        )
    assert response.status_code == 200
