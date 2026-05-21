from forhacker.data.models import Agent, Case, EvidenceIndex, Finding


def test_case_table_exists():
    assert hasattr(Case, "__tablename__")
    assert Case.__tablename__ == "cases"


def test_finding_has_confidence_columns():
    assert hasattr(Finding, "task_confidence")
    assert hasattr(Finding, "evidence_confidence")
    assert hasattr(Finding, "last_ingested_at")


def test_evidence_index_has_integrity_field():
    assert hasattr(EvidenceIndex, "integrity")


def test_agent_has_heartbeat_field():
    assert hasattr(Agent, "last_heartbeat")
