from forhacker.collab.shared import read_dag_checkpoint, read_findings, write_dag_checkpoint, write_finding


def test_write_and_read_finding(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    write_finding(
        case_dir,
        member_id="member-A",
        finding={
            "id": "member-A-F-001",
            "type": "memory_analysis",
            "summary": "Suspicious process detected",
            "task_confidence": "HIGH",
            "evidence_confidence": "verified",
        },
    )
    findings = read_findings(case_dir, member_id="member-A")
    assert len(findings) == 1
    assert findings[0]["id"] == "member-A-F-001"
    assert findings[0]["evidence_confidence"] == "verified"


def test_read_findings_returns_empty_for_new_member(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    findings = read_findings(case_dir, member_id="no-one")
    assert findings == []


def test_write_dag_checkpoint(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    write_dag_checkpoint(
        case_dir,
        tasks=[
            {"task_id": "T-001", "type": "analysis", "status": "done", "depends_on": []},
        ],
    )
    tasks = read_dag_checkpoint(case_dir)
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "T-001"


def test_schema_version_written(tmp_shared_dir):
    case_dir = tmp_shared_dir / "cases" / "case-1"
    case_dir.mkdir(parents=True)
    import yaml

    write_finding(case_dir, member_id="member-A", finding={"id": "A-F-001", "type": "test"})
    path = case_dir / "findings" / "member-A.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
