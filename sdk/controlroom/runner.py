"""Eval runner: executes a Dataset against a user-provided LLM and scores each output."""

import logging
from typing import Callable

from controlroom.client import send_results
from controlroom.dataset import Dataset, TestCase
from controlroom.models import EvalResult, TestCaseResult
from controlroom.scorer import score_output

logger = logging.getLogger(__name__)


def run_eval(
    dataset: Dataset,
    llm: Callable[[str], str],
    run_name: str,
    model_name: str = "unknown",
) -> EvalResult:
    """Run every TestCase in `dataset` through `llm`, score each output, and return an EvalResult.

    For each TestCase, the LLM is called with the input; the actual output is then passed
    to the judge via score_output to produce a TestCaseResult. If the LLM call raises,
    the failure is caught and recorded as a failing TestCaseResult with confidence 0.0.

    Args:
        dataset: The Dataset of TestCase objects to evaluate.
        llm: A callable taking an input string and returning the LLM's output string.
        run_name: Human-readable name identifying this eval run.
        model_name: Identifier for the LLM under evaluation (e.g. "gpt-4o").

    Returns:
        An EvalResult aggregating per-case results and pass/fail counts.
    """
    results: list[TestCaseResult] = []
    passed_count: int = 0
    failed_count: int = 0

    testcase: TestCase
    for testcase in dataset:
        try:
            actual: str = llm(testcase.input)
        except Exception as error:
            logger.warning("LLM call failed for input %r: %s", testcase.input, error)
            result = TestCaseResult(
                input=testcase.input,
                expected=testcase.expected,
                actual="",
                passed=False,
                confidence=0.0,
                reasoning=f"LLM call failed: {error}",
            )
        else:
            result = score_output(testcase.input, testcase.expected, actual)

        results.append(result)
        if result.passed:
            passed_count += 1
        else:
            failed_count += 1

    eval_result = EvalResult(
        run_name=run_name,
        model_name=model_name,
        total=len(results),
        passed=passed_count,
        failed=failed_count,
        results=results,
    )

    run_id: str | None = send_results(eval_result)
    if run_id is not None:
        logger.info("Eval results sent to Control Room. Run ID: %s", run_id)
    else:
        logger.warning(
            "Could not send results to Control Room backend. Results available locally only."
        )

    return eval_result
