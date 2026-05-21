from forhacker.meta.audit import AuditTrail


def test_audit_trail_append_and_read():
    trail = AuditTrail()
    trail.log(action="plugin_install", actor="admin", target="forensics-memory", details={"version": "0.1.0"})
    entries = trail.entries()
    assert len(entries) == 1
    assert entries[0]["action"] == "plugin_install"
    assert entries[0]["actor"] == "admin"


def test_audit_trail_rollback_records():
    trail = AuditTrail()
    trail.snapshot("pre-install-snapshot")
    trail.log(action="install", actor="meta-agent", target="plugin-x")
    assert trail.latest_snapshot() == "pre-install-snapshot"
