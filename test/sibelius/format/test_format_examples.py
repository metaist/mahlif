"""Test runner for ManuScript format examples.

This module reads `.md` files from `test/sibelius/format/examples/` and runs
format tests based on input/expected pairs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from mahlif.sibelius.manuscript.format import format_plugin

EXAMPLES_DIR = Path(__file__).parent / "examples"


def parse_format_examples(md_path: Path) -> list[tuple[str, str, str]]:
    """Parse format examples from a markdown file.

    Args:
        md_path: Path to markdown file

    Returns:
        List of (test_name, input_code, expected_code) tuples
    """
    content = md_path.read_text()
    examples: list[tuple[str, str, str]] = []

    # Pattern to match test cases
    # ## Test Name
    # ...
    # **Input:**
    # ```manuscript
    # code
    # ```
    # **Expected:**
    # ```manuscript
    # code
    # ```
    test_pattern = re.compile(
        r"^## (.+?)$.*?"
        r"\*\*Input:\*\*\s*```manuscript\s*\n(.*?)```\s*"
        r"\*\*Expected:\*\*\s*```manuscript\s*\n(.*?)```",
        re.MULTILINE | re.DOTALL,
    )

    for match in test_pattern.finditer(content):
        test_name = match.group(1).strip()
        input_code = match.group(2)
        expected_code = match.group(3)
        examples.append((test_name, input_code, expected_code))

    return examples


def collect_all_examples() -> list[tuple[str, str, str, str]]:
    """Collect all format examples from markdown files.

    Returns:
        List of (file_name, test_name, input_code, expected_code) tuples
    """
    all_examples: list[tuple[str, str, str, str]] = []

    for md_file in sorted(EXAMPLES_DIR.glob("*.md")):
        if md_file.name == "README.md":
            continue

        file_name = md_file.stem
        examples = parse_format_examples(md_file)
        for test_name, input_code, expected_code in examples:
            all_examples.append((file_name, test_name, input_code, expected_code))

    return all_examples


EXAMPLE_TESTS = collect_all_examples()


@pytest.mark.parametrize(
    "file_name,test_name,input_code,expected_code",
    EXAMPLE_TESTS,
    ids=[f"{t[0]}::{t[1]}" for t in EXAMPLE_TESTS],
)
def test_format_example(
    file_name: str,
    test_name: str,
    input_code: str,
    expected_code: str,
) -> None:
    """Test format example from markdown file.

    Args:
        file_name: Name of the source markdown file
        test_name: Name of the test case
        input_code: Input ManuScript code
        expected_code: Expected formatted code
    """
    actual = format_plugin(input_code)

    if actual != expected_code:
        # Show detailed diff
        import difflib

        diff = difflib.unified_diff(
            expected_code.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile="expected",
            tofile="actual",
        )
        diff_str = "".join(diff)
        pytest.fail(
            f"Test: {file_name}::{test_name}\n"
            f"Formatting mismatch:\n{diff_str}\n"
            f"Expected:\n{expected_code!r}\n"
            f"Actual:\n{actual!r}"
        )
