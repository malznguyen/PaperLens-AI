from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "PaperLens AI API"
    assert payload["environment"] == "development"
    assert isinstance(datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")), datetime)
