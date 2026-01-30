"""Tests for check_method_body() API parameters."""

from __future__ import annotations

from mahlif.sibelius.manuscript.checker import check_method_body
from mahlif.sibelius.manuscript.errors import LintError


def syntax_errors(errors: list[LintError]) -> list[LintError]:
    """Filter to only syntax errors, excluding semantic warnings."""
    excluded = {"MS-W025", "MS-W030", "MS-W033"}  # unused var, empty stmt, shadowing
    return [e for e in errors if e.code not in excluded]


def test_empty_body() -> None:
    """Test empty method body is valid."""
    errors = check_method_body("")
    assert syntax_errors(errors) == []


def test_with_parameters() -> None:
    """Test parameters are treated as defined."""
    errors = check_method_body("x = a + b;", parameters=["a", "b"])
    assert not any(e.code == "MS-W020" for e in errors)


def test_with_global_vars() -> None:
    """Test global_vars are treated as defined."""
    errors = check_method_body("x = MyGlobal;", global_vars={"MyGlobal"})
    assert not any(e.code == "MS-W020" for e in errors)


def test_line_col_offset() -> None:
    """Test that line/col offsets are applied to errors."""
    errors = check_method_body("x = undefined;", start_line=10, start_col=5)
    assert errors[0].line >= 10


def test_method_name_in_context() -> None:
    """Test method name is stored (for potential future use)."""
    errors = check_method_body("x = 1;", method_name="TestMethod")
    assert syntax_errors(errors) == []
