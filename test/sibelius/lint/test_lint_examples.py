"""Test runner for ManuScript lint examples.

This module reads `.md` files from `test/sibelius/lint/examples/` and runs lint tests
based on the code blocks and expected errors defined in each file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from mahlif.sibelius.manuscript.lint import lint


EXAMPLES_DIR = Path(__file__).parent / "examples"


def parse_example_file(path: Path) -> list[tuple[str, str, set[str]]]:
    """Parse an example markdown file into test cases.

    Args:
        path: Path to the markdown file

    Returns:
        List of (test_name, code, expected_codes) tuples
    """
    content = path.read_text(encoding="utf-8")
    tests: list[tuple[str, str, set[str]]] = []

    # Split by ## headings (test cases)
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip content before first ##
        lines = section.strip().split("\n")
        if not lines:
            continue

        test_name = lines[0].strip()

        # Find code block
        code_match = re.search(r"```manuscript\n(.*?)```", section, re.DOTALL)
        if not code_match:
            continue

        code = code_match.group(1)

        # Find expected errors
        expected_codes: set[str] = set()
        errors_match = re.search(
            r"\*\*Expected errors:\*\*\n(.*?)(?:\n\n|\n\*\*|$)",
            section,
            re.DOTALL,
        )
        if errors_match:
            errors_text = errors_match.group(1)
            # Match error codes like MS-E040, MS-W002
            for match in re.finditer(r"`(MS-[EWT]\d{3})`", errors_text):
                expected_codes.add(match.group(1))

            # Check for "(none)" to indicate no errors expected
            if "(none)" in errors_text.lower():
                expected_codes = set()

        tests.append((test_name, code, expected_codes))

    return tests


def collect_example_tests() -> list[tuple[str, str, str, set[str]]]:
    """Collect all test cases from example files.

    Returns:
        List of (file_name, test_name, code, expected_codes) tuples
    """
    tests: list[tuple[str, str, str, set[str]]] = []

    if not EXAMPLES_DIR.exists():
        return tests

    for md_file in sorted(EXAMPLES_DIR.glob("*.md")):
        if md_file.name == "README.md":
            continue

        file_tests = parse_example_file(md_file)
        for test_name, code, expected_codes in file_tests:
            tests.append((md_file.stem, test_name, code, expected_codes))

    return tests


# Collect tests at module load time
EXAMPLE_TESTS = collect_example_tests()


@pytest.mark.parametrize(
    "file_name,test_name,code,expected_codes",
    EXAMPLE_TESTS,
    ids=[f"{t[0]}::{t[1]}" for t in EXAMPLE_TESTS],
)
def test_lint_example(
    file_name: str,
    test_name: str,
    code: str,
    expected_codes: set[str],
    tmp_path: Path,
) -> None:
    """Test lint example from markdown file.

    Args:
        file_name: Name of the source markdown file
        test_name: Name of the test case
        code: ManuScript code to lint
        expected_codes: Set of expected error codes
        tmp_path: Pytest temporary directory
    """
    # Write code to temp file
    plg_file = tmp_path / "test.plg"
    plg_file.write_text(code, encoding="utf-8")

    # Run linter
    errors = lint(plg_file)
    # Filter out MS-W025 (unused variable) from example tests since
    # minimal code snippets often have variables that aren't fully used
    errors = [e for e in errors if e.code != "MS-W025"]
    actual_codes = {e.code for e in errors}

    # Compare
    missing = expected_codes - actual_codes
    extra = actual_codes - expected_codes

    if missing or extra:
        msg_parts = [f"Test: {file_name}::{test_name}"]
        if missing:
            msg_parts.append(f"Missing expected errors: {sorted(missing)}")
        if extra:
            msg_parts.append(f"Unexpected errors: {sorted(extra)}")
        msg_parts.append(f"Actual errors: {[str(e) for e in errors]}")
        pytest.fail("\n".join(msg_parts))


def test_parse_simple_example(tmp_path: Path) -> None:
    """Test parsing a simple example file."""
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Test File

## Test Case One

Description here.

```manuscript
{ code }
```

**Expected errors:**
- `MS-E001` - Some error
- `MS-W002` - Some warning
"""
    )

    tests = parse_example_file(md_file)
    assert len(tests) == 1
    name, code, expected = tests[0]
    assert name == "Test Case One"
    assert "{ code }" in code
    assert expected == {"MS-E001", "MS-W002"}


def test_parse_no_errors_expected(tmp_path: Path) -> None:
    """Test parsing example with no errors expected."""
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Test File

## Valid Code

```manuscript
{ valid }
```

**Expected errors:**
(none)
"""
    )

    tests = parse_example_file(md_file)
    assert len(tests) == 1
    _, _, expected = tests[0]
    assert expected == set()


def test_parse_multiple_tests(tmp_path: Path) -> None:
    """Test parsing file with multiple test cases."""
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """# Test File

## First Test

```manuscript
{ first }
```

**Expected errors:**
- `MS-E001` - Error one

## Second Test

```manuscript
{ second }
```

**Expected errors:**
- `MS-W002` - Warning two
"""
    )

    tests = parse_example_file(md_file)
    assert len(tests) == 2
    assert tests[0][0] == "First Test"
    assert tests[0][2] == {"MS-E001"}
    assert tests[1][0] == "Second Test"
    assert tests[1][2] == {"MS-W002"}
