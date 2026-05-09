"""Smoke test: run a tiny dataset through run_eval with a dummy LLM."""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "sdk"))

from controlroom import Dataset, run_eval


CASES: list[dict[str, str]] = [
    {"input": "What is the capital of France?", "expected": "Paris"},
    {"input": "What is 2 + 2?", "expected": "4"},
    {"input": "What is the color of the sky?", "expected": "blue"},
]


def dummy_llm(prompt: str) -> str:
    answers = {
        "What is the capital of France?": "London",  # wrong
        "What is 2 + 2?": "4",                        # correct
        "What is the color of the sky?": "green",     # wrong
    }
    return answers[prompt]


def main() -> None:
    dataset = Dataset(CASES)
    results = run_eval(
    dataset=dataset, 
    llm=dummy_llm, 
    run_name="dummy-smoke-test",
    model_name="groq/llama-3.1-8b-instant"
)
    print(json.dumps(results.model_dump(), indent=2))


if __name__ == "__main__":
    main()
