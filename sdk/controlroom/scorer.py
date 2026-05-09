"""LLM-as-judge scoring for Control Room test case outputs."""

import os
import json
import logging

from groq import Groq

from controlroom.models import TestCaseResult

logger = logging.getLogger(__name__)

_JUDGE_API_KEY: str | None = os.environ.get("CONTROLROOM_JUDGE_API_KEY")
_JUDGE_MODEL: str = os.environ.get("CONTROLROOM_JUDGE_MODEL", "llama-3.3-70b-versatile")

_client: Groq | None = None


def _get_client() -> Groq:
    """Lazily construct and return a cached Groq judge client."""
    global _client
    if not _JUDGE_API_KEY:
        raise ValueError("CONTROLROOM_JUDGE_API_KEY environment variable is not set.")
    if _client is None:
        _client = Groq(api_key=_JUDGE_API_KEY)
    return _client


def score_output(prompt_input: str, expected: str, actual: str) -> TestCaseResult:
    """Judge whether ``actual`` semantically matches ``expected`` for the given ``prompt_input``.

    Sends the trio to the configured Groq judge model and asks for a strict
    JSON verdict. Retries once if the first response is not valid JSON, and
    falls back to a failed result if the second attempt also fails.
    """
    client = _get_client()

    prompt = (
        "You are an expert LLM evaluator. Given an input, expected \n"
        "output, and actual output, determine if the actual output is \n"
        "correct. Respond ONLY with a JSON object with exactly three \n"
        "keys: pass (boolean), confidence (float 0.0-1.0), reasoning \n"
        "(string). No markdown, no backticks, raw JSON only.\n"
        "\n"
        f"Input: {prompt_input}\n"
        f"Expected: {expected}\n"
        f"Actual: {actual}"
    )

    parsed: dict | None = None
    for attempt in range(2):
        response = client.chat.completions.create(
            model=_JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        try:
            parsed = json.loads(response.choices[0].message.content)
            break
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Judge returned invalid JSON on attempt %d: %s", attempt + 1, exc)
            parsed = None

    if parsed is None:
        return TestCaseResult(
            input=prompt_input,
            expected=expected,
            actual=actual,
            passed=False,
            confidence=0.0,
            reasoning="Judge returned invalid JSON after retry.",
        )

    return TestCaseResult(
        input=prompt_input,
        expected=expected,
        actual=actual,
        passed=bool(parsed["pass"]),
        confidence=float(parsed["confidence"]),
        reasoning=str(parsed["reasoning"]),
    )
