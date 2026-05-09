"""Eval run REST API endpoints."""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models import EvalRun, TestResult

router = APIRouter()


class TestCaseResultIn(BaseModel):
    """Per-test-case payload mirroring sdk.controlroom.models.TestCaseResult."""

    input: str
    expected: str
    actual: str
    passed: bool
    confidence: float
    reasoning: str


class EvalResultIn(BaseModel):
    """Eval run payload mirroring sdk.controlroom.models.EvalResult."""

    run_name: str
    model_name: str = "unknown"
    total: int
    passed: int
    failed: int
    results: List[TestCaseResultIn]


class EvalRunSummary(BaseModel):
    """Summary view of an eval run used in list and detail responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_name: str
    model_name: Optional[str]
    created_at: datetime
    total_cases: int
    passed: int
    failed: int


class TestResultOut(BaseModel):
    """Per-test-case row in an eval run detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    input: str
    expected: str
    actual: str
    passed: bool
    confidence: float
    reasoning: str
    created_at: datetime


class EvalRunDetail(EvalRunSummary):
    """Detail view of an eval run including all per-test-case results."""

    results: List[TestResultOut]


@router.post("/runs")
def create_run(payload: EvalResultIn, db: Session = Depends(get_db)) -> dict:
    """Persist an eval run and all of its per-test-case results."""
    run = EvalRun(
        run_name=payload.run_name,
        model_name=payload.model_name,
        total_cases=payload.total,
        passed=payload.passed,
        failed=payload.failed,
    )
    db.add(run)
    db.flush()

    for case in payload.results:
        db.add(
            TestResult(
                run_id=run.id,
                input=case.input,
                expected=case.expected,
                actual=case.actual,
                passed=case.passed,
                confidence=case.confidence,
                reasoning=case.reasoning,
            )
        )

    db.commit()
    return {"run_id": str(run.id)}


@router.get("/runs", response_model=List[EvalRunSummary])
def list_runs(db: Session = Depends(get_db)) -> List[EvalRun]:
    """Return all eval runs ordered by creation time, newest first."""
    return db.query(EvalRun).order_by(EvalRun.created_at.desc()).all()


@router.get("/runs/{run_id}", response_model=EvalRunDetail)
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)) -> EvalRunDetail:
    """Return one eval run with all of its per-test-case results, or 404."""
    run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="Eval run not found")

    results = db.query(TestResult).filter(TestResult.run_id == run_id).all()

    return EvalRunDetail(
        id=run.id,
        run_name=run.run_name,
        model_name=run.model_name,
        created_at=run.created_at,
        total_cases=run.total_cases,
        passed=run.passed,
        failed=run.failed,
        results=[TestResultOut.model_validate(r) for r in results],
    )
