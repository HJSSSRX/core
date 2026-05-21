import os
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = 1


def _write_yaml_atomic(path: Path, data: dict):
    data["schema_version"] = SCHEMA_VERSION
    payload = yaml.dump(data, allow_unicode=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    # Accept version N and N-1
    version = data.get("schema_version", 1)
    if version not in (SCHEMA_VERSION, SCHEMA_VERSION - 1):
        raise ValueError(f"Unsupported schema_version: {version}")
    return data


def write_finding(case_dir: Path, member_id: str, finding: dict):
    findings_dir = case_dir / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)
    path = findings_dir / f"{member_id}.yaml"
    existing = _read_yaml(path)
    existing.setdefault("findings", []).append(finding)
    _write_yaml_atomic(path, {"findings": existing["findings"]})


def read_findings(case_dir: Path, member_id: str) -> list[dict[str, Any]]:
    path = case_dir / "findings" / f"{member_id}.yaml"
    data = _read_yaml(path)
    return data.get("findings", [])


def write_dag_checkpoint(case_dir: Path, tasks: list[dict[str, Any]]):
    path = case_dir / "dag_state.yaml"
    _write_yaml_atomic(path, {"tasks": tasks})


def read_dag_checkpoint(case_dir: Path) -> list[dict[str, Any]]:
    data = _read_yaml(case_dir / "dag_state.yaml")
    return data.get("tasks", [])


def write_heartbeat(case_dir: Path, agent_id: str):
    import datetime
    path = case_dir / "agents" / agent_id / "heartbeat.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_yaml_atomic(path, {
        "agent_id": agent_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })


def check_heartbeat(case_dir: Path, agent_id: str, staleness_seconds: float = 90.0) -> bool:
    import datetime
    path = case_dir / "agents" / agent_id / "heartbeat.yaml"
    if not path.exists():
        return False
    data = _read_yaml(path)
    ts = datetime.datetime.fromisoformat(data["timestamp"])
    return (datetime.datetime.now(datetime.timezone.utc) - ts).total_seconds() < staleness_seconds
