import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    lead_investigator = Column(String, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    type = Column(String, nullable=False)
    status = Column(String, default="pending")
    assigned_to = Column(String, nullable=True)
    task_confidence = Column(String, default="MEDIUM")  # HIGH | MEDIUM | LOW
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    type = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    task_confidence = Column(String, default="MEDIUM")  # HIGH | MEDIUM | LOW
    evidence_confidence = Column(String, default="unknown")  # verified | inferred | unknown
    evidence_ref = Column(String, nullable=True)
    created_by = Column(String, nullable=False)
    last_ingested_at = Column(DateTime, nullable=True)


class EvidenceIndex(Base):
    __tablename__ = "evidence_index"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    path = Column(String, nullable=False)
    sha256 = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    indexed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    integrity = Column(String, default="missing")  # verified | failed | missing | orphan


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    cell = Column(String, nullable=True)
    status = Column(String, default="alive")
    last_heartbeat = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    target = Column(String, nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class MetaProposal(Base):
    __tablename__ = "meta_proposals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=True)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")
    risk_level = Column(String, default="LOW")
    approved_by = Column(String, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    rollback_snapshot = Column(String, nullable=True)


class MetaScanLock(Base):
    __tablename__ = "meta_scan_lock"
    id = Column(Integer, primary_key=True, autoincrement=True)
    locked_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    locked_by = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
