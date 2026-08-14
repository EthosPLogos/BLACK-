"""
SQLAlchemy ORM models for Mr. Black persistent storage.

Tables:
  audit_events    — structured audit log (mirrors black_audit.jsonl)
  approvals       — action approval queue (mirrors black_approvals.json)
  research_notes  — finance research runs from /api/finance/research
  schedule_tasks  — scheduled task registry (mirrors black_schedule.json)
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(16), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_session_type", "session_id", "event_type"),
    )


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True)  # UUID
    user_input = Column(Text, nullable=False)
    policy_reason = Column(Text, nullable=True)
    trust_level = Column(String(16), nullable=True)
    domain = Column(String(32), nullable=True)
    task_type = Column(String(32), nullable=True)
    status = Column(String(16), default="pending", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class ResearchNote(Base):
    __tablename__ = "research_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    signal = Column(String(16), nullable=True)   # bullish | bearish | neutral
    confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    reasoning_steps = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False, index=True)


class ScheduleTask(Base):
    __tablename__ = "schedule_tasks"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    cron = Column(String(64), nullable=True)
    task_type = Column(String(32), nullable=True)
    payload = Column(JSON, nullable=True)
    enabled = Column(Integer, default=1)  # 1=enabled, 0=disabled
    last_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
