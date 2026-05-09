"""Pydantic models for evaluation results returned by the SDK."""

from pydantic import BaseModel, Field


class TestCaseResult(BaseModel):
    """The outcome of running a single test case through the LLM and judge."""

    input: str = Field(..., description="The input prompt sent to the LLM.")
    expected: str = Field(..., description="The expected output for this test case.")
    actual: str = Field(..., description="The actual output produced by the LLM.")
    passed: bool = Field(..., description="Whether the judge marked the actual output as correct.")
    confidence: float = Field(..., description="Judge confidence score between 0.0 and 1.0.")
    reasoning: str = Field(..., description="The judge's natural-language reasoning for its verdict.")


class EvalResult(BaseModel):
    """The aggregated outcome of one full evaluation run over a dataset."""

    run_name: str = Field(..., description="Human-readable name identifying this eval run.")
    model_name: str = Field("unknown", description="Identifier for the LLM under evaluation.")
    total: int = Field(..., description="Total number of test cases executed in this run.")
    passed: int = Field(..., description="Number of test cases the judge marked as passed.")
    failed: int = Field(..., description="Number of test cases the judge marked as failed.")
    results: list[TestCaseResult] = Field(..., description="Per-test-case results in execution order.")
