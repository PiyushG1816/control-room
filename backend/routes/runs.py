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


class CompareRunInfo(BaseModel):
    """Minimal run identification used in compare responses."""

    id: uuid.UUID
    run_name: str
    model_name: Optional[str]


class CompareResultSide(BaseModel):
    """One side of a per-input comparison entry."""

    actual: str
    passed: bool
    confidence: float
    reasoning: str


class ComparisonEntry(BaseModel):
    """Aligned result for a single input that exists in both runs."""

    input: str
    expected: str
    result_a: CompareResultSide
    result_b: CompareResultSide
    status: str


class CompareSummary(BaseModel):
    """Aggregate counts across all aligned comparison entries."""

    total_compared: int
    regressions: int
    improvements: int
    unchanged: int


class CompareResponse(BaseModel):
    """Top-level response for GET /compare."""

    run_a: CompareRunInfo
    run_b: CompareRunInfo
    comparisons: List[ComparisonEntry]
    summary: CompareSummary


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


@router.get("/compare", response_model=CompareResponse)
def compare_runs(
    run_a: uuid.UUID,
    run_b: uuid.UUID,
    db: Session = Depends(get_db),
) -> CompareResponse:
    """Compare two eval runs by aligning their test cases on input text.

    Fetches both ``EvalRun`` records (404 if either is missing) and the
    full set of ``TestResult`` rows for each. Aligns results on identical
    input strings — only inputs present in both runs appear in the
    response. Each aligned entry is classified as ``regression`` (A passed,
    B failed), ``improvement`` (A failed, B passed), or ``unchanged``
    (both passed or both failed). The summary contains aggregate counts.
    """
    eval_run_a: Optional[EvalRun] = (
        db.query(EvalRun).filter(EvalRun.id == run_a).first()
    )
    if eval_run_a is None:
        raise HTTPException(status_code=404, detail="Eval run A not found")

    eval_run_b: Optional[EvalRun] = (
        db.query(EvalRun).filter(EvalRun.id == run_b).first()
    )
    if eval_run_b is None:
        raise HTTPException(status_code=404, detail="Eval run B not found")

    results_a: List[TestResult] = (
        db.query(TestResult).filter(TestResult.run_id == run_a).all()
    )
    results_b: List[TestResult] = (
        db.query(TestResult).filter(TestResult.run_id == run_b).all()
    )

    by_input_a: dict[str, TestResult] = {r.input: r for r in results_a}
    by_input_b: dict[str, TestResult] = {r.input: r for r in results_b}
    shared_inputs: List[str] = [i for i in by_input_a if i in by_input_b]

    comparisons: List[ComparisonEntry] = []
    regressions = 0
    improvements = 0
    unchanged = 0

    for input_text in shared_inputs:
        row_a = by_input_a[input_text]
        row_b = by_input_b[input_text]

        if row_a.passed and not row_b.passed:
            status = "regression"
            regressions += 1
        elif not row_a.passed and row_b.passed:
            status = "improvement"
            improvements += 1
        else:
            status = "unchanged"
            unchanged += 1

        comparisons.append(
            ComparisonEntry(
                input=input_text,
                expected=row_a.expected,
                result_a=CompareResultSide(
                    actual=row_a.actual,
                    passed=row_a.passed,
                    confidence=row_a.confidence,
                    reasoning=row_a.reasoning,
                ),
                result_b=CompareResultSide(
                    actual=row_b.actual,
                    passed=row_b.passed,
                    confidence=row_b.confidence,
                    reasoning=row_b.reasoning,
                ),
                status=status,
            )
        )

    return CompareResponse(
        run_a=CompareRunInfo(
            id=eval_run_a.id,
            run_name=eval_run_a.run_name,
            model_name=eval_run_a.model_name,
        ),
        run_b=CompareRunInfo(
            id=eval_run_b.id,
            run_name=eval_run_b.run_name,
            model_name=eval_run_b.model_name,
        ),
        comparisons=comparisons,
        summary=CompareSummary(
            total_compared=len(comparisons),
            regressions=regressions,
            improvements=improvements,
            unchanged=unchanged,
        ),
    )
