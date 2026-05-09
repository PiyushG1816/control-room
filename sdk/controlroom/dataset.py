"""Dataset and TestCase definitions for Control Room evaluations."""

from typing import Iterator

from pydantic import BaseModel


class TestCase(BaseModel):
    """A single evaluation test case pairing an input with its expected output."""

    input: str
    expected: str


class Dataset:
    """A collection of TestCase objects to be run against an LLM."""

    def __init__(self, cases: list[dict]) -> None:
        """Build a Dataset from a list of dicts, each with 'input' and 'expected' keys.

        Raises:
            ValueError: If any dict is missing the 'input' or 'expected' key.
        """
        self._cases: list[TestCase] = []
        for index, case in enumerate(cases):
            if "input" not in case or "expected" not in case:
                raise ValueError(
                    f"Case at index {index} is missing 'input' or 'expected' key."
                )
            self._cases.append(TestCase(input=case["input"], expected=case["expected"]))

    def __len__(self) -> int:
        """Return the number of test cases in the dataset."""
        return len(self._cases)

    def __iter__(self) -> Iterator[TestCase]:
        """Iterate over the TestCase objects in the dataset."""
        return iter(self._cases)
