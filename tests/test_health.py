import requests

def test_health_local():
    # This test is meant to be run in a container or runner which can reach the app.
    # For CodeBuild you can spin up the app as part of the test stage or mock responses.
    # As a safe quick test, ensure the health endpoint responds if the app is running locally.
    resp = requests.get("http://127.0.0.1:5000/health", timeout=3)
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data