from fastapi.testclient import TestClient

from forhacker.cli.web.app import app

client = TestClient(app)


def test_dashboard_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "ForHacker" in response.text


def test_case_overview_empty_state():
    response = client.get("/case/test-case")
    assert response.status_code == 200
    assert "No active case" in response.text or "test-case" in response.text
