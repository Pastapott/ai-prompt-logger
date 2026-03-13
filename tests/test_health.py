from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import app


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "ok"
    assert "version" in data