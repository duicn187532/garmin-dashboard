from fastapi.testclient import TestClient

from app.main import app


def test_status_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

