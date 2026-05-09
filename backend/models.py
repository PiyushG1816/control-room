"""SQLAlchemy ORM models for Control Room eval runs and per-test-case results."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class EvalRun(Base):
    """One execution of a dataset against a single LLM."""

    __tablename__ = "eval_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_name = Column(String, nullable=False)
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_cases = Column(Integer)
    passed = Column(Integer)
    failed = Column(Integer)


class TestResult(Base):
    """The judge verdict for a single test case within an eval run."""

    __tablename__ = "test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("eval_runs.id"), nullable=False)
    input = Column(Text, nullable=False)
    expected = Column(Text, nullable=False)
    actual = Column(Text, nullable=False)
    passed = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
