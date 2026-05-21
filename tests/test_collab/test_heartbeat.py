from forhacker.collab.shared import write_heartbeat, check_heartbeat


def test_heartbeat_write_and_check(tmp_path):
    case_dir = tmp_path / "test-case"
    case_dir.mkdir()
    write_heartbeat(case_dir, "agent-1")
    assert check_heartbeat(case_dir, "agent-1", staleness_seconds=90.0)
    assert not check_heartbeat(case_dir, "agent-1", staleness_seconds=-1.0)
    assert not check_heartbeat(case_dir, "nonexistent", staleness_seconds=90.0)
