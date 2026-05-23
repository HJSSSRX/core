from __future__ import annotations

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
    assert "test-case" in response.text


def test_case_overview_with_dag(tmp_path):
    cases_dir = tmp_path / "shared" / "cases" / "realcase"
    cases_dir.mkdir(parents=True)
    import yaml

    (cases_dir / "dag_state.yaml").write_text(
        yaml.dump(
            {
                "tasks": [
                    {"id": "1", "status": "done", "name": "collect"},
                    {"id": "2", "status": "running", "name": "analyze"},
                    {"id": "3", "status": "failed", "name": "report"},
                ]
            }
        ),
        encoding="utf-8",
    )

    import forhacker.cli.web.app as app_mod

    old_shared = app_mod.SHARED_DIR
    try:
        app_mod.SHARED_DIR = tmp_path / "shared"
        response = client.get("/case/realcase")
        assert response.status_code == 200
        assert "realcase" in response.text
        assert "collect" in response.text or "done" in response.text.lower()
    finally:
        app_mod.SHARED_DIR = old_shared


def test_case_overview_with_findings(tmp_path):
    cases_dir = tmp_path / "shared" / "cases" / "foundcase"
    cases_dir.mkdir(parents=True)
    import yaml

    (cases_dir / "dag_state.yaml").write_text(
        yaml.dump({"tasks": [{"id": "1", "status": "done"}]}),
        encoding="utf-8",
    )
    findings_dir = cases_dir / "findings"
    findings_dir.mkdir()
    (findings_dir / "task_1.yaml").write_text(
        yaml.dump({"findings": [{"type": "file", "path": "/tmp/malware.exe", "hash": "abc123"}]}),
        encoding="utf-8",
    )

    import forhacker.cli.web.app as app_mod

    old_shared = app_mod.SHARED_DIR
    try:
        app_mod.SHARED_DIR = tmp_path / "shared"
        response = client.get("/case/foundcase")
        assert response.status_code == 200
        assert "foundcase" in response.text
    finally:
        app_mod.SHARED_DIR = old_shared


def test_kb_index_empty():
    response = client.get("/kb")
    assert response.status_code == 200


def test_kb_index_with_search():
    response = client.get("/kb?q=malware")
    assert response.status_code == 200


def test_kb_index_with_tag():
    response = client.get("/kb?tag=forensics")
    assert response.status_code == 200


def test_kb_entry_not_found():
    response = client.get("/kb/nonexistent_entry_id")
    assert response.status_code == 404


def test_timeline():
    response = client.get("/timeline")
    assert response.status_code == 200


def test_timeline_with_cases(tmp_path):
    cases_dir = tmp_path / "shared" / "cases" / "timelinecase"
    cases_dir.mkdir(parents=True)
    findings_dir = cases_dir / "findings"
    findings_dir.mkdir()
    import yaml

    (findings_dir / "task_1.yaml").write_text(
        yaml.dump({"findings": [{"type": "timeline_event", "timestamp": "2024-01-01T00:00:00", "event": "Login"}]}),
        encoding="utf-8",
    )

    import forhacker.cli.web.app as app_mod

    old_shared = app_mod.SHARED_DIR
    try:
        app_mod.SHARED_DIR = tmp_path / "shared"
        response = client.get("/timeline")
        assert response.status_code == 200
    finally:
        app_mod.SHARED_DIR = old_shared


def test_evidence_map_no_case():
    response = client.get("/evidence/nonexistent_case")
    assert response.status_code == 200
    assert "evidence_count" in response.text or "Evidence" in response.text


def test_evidence_map_with_files(tmp_path):
    evidence_dir = tmp_path / "shared" / "cases" / "evcase" / "evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "image.dd").write_bytes(b"\x00" * 100)
    subdir = evidence_dir / "logs"
    subdir.mkdir()
    (subdir / "system.log").write_text("log data", encoding="utf-8")

    import forhacker.cli.web.app as app_mod

    old_shared = app_mod.SHARED_DIR
    try:
        app_mod.SHARED_DIR = tmp_path / "shared"
        response = client.get("/evidence/evcase")
        assert response.status_code == 200
        assert "image.dd" in response.text
        assert "100" in response.text  # file size
    finally:
        app_mod.SHARED_DIR = old_shared


def test_status_page():
    response = client.get("/status")
    assert response.status_code == 200
    assert "Plugins" in response.text or "Status" in response.text


def test_api_status_json():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "plugins" in data
    assert "cases" in data
    assert "kb_entries" in data
    assert "proposals" in data


def test_web_app_routes_exist():
    """Verify all major routes return non-500 responses."""
    routes = [
        "/",
        "/kb",
        "/kb?q=test",
        "/timeline",
        "/status",
        "/api/status",
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code != 500, f"Route {route} returned 500"
