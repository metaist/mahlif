"""Tests for statement parsing in checker."""

from __future__ import annotations

from mahlif.sibelius.manuscript.checker import check_method_body
from mahlif.sibelius.manuscript.errors import LintError


def syntax_errors(errors: list[LintError]) -> list[LintError]:
    """Filter to only syntax errors, excluding semantic warnings."""
    excluded = {"MS-W025", "MS-W030", "MS-W033"}
    return [e for e in errors if e.code not in excluded]


# =============================================================================
# Basic statement parsing
# =============================================================================


def test_simple_assignment() -> None:
    """Test simple assignment parses without error."""
    errors = check_method_body("x = 1;")
    assert syntax_errors(errors) == []


def test_method_call() -> None:
    """Test method call parses without error."""
    errors = check_method_body("Sibelius.MessageBox('hello');")
    assert syntax_errors(errors) == []


def test_return_statement() -> None:
    """Test return statement parses without error."""
    errors = check_method_body("return True;")
    assert syntax_errors(errors) == []


def test_multiple_statements() -> None:
    """Test multiple statements parse without error."""
    code = "x = 1; y = 2; z = x + y;"
    errors = check_method_body(code)
    assert syntax_errors(errors) == []


# =============================================================================
# Control flow
# =============================================================================


def test_if_statement() -> None:
    """Test valid if statement."""
    errors = check_method_body("x = 1; if (x) { y = 1; }")
    assert syntax_errors(errors) == []


def test_while_statement() -> None:
    """Test valid while statement."""
    errors = check_method_body("x = 5; while (x > 0) { x = x - 1; }")
    assert syntax_errors(errors) == []


def test_for_statement() -> None:
    """Test valid for statement."""
    errors = check_method_body("for i = 1 to 10 { x = i; }")
    assert syntax_errors(errors) == []


def test_for_each_statement() -> None:
    """Test valid for each statement."""
    errors = check_method_body(
        "list = CreateSparseArray(); for each item in list { x = item; }"
    )
    assert syntax_errors(errors) == []


def test_for_each_with_type() -> None:
    """Test for each with type annotation."""
    errors = check_method_body("for each Note n in bar { x = n; }", parameters=["bar"])
    assert syntax_errors(errors) == []


def test_switch_statement() -> None:
    """Test valid switch statement."""
    errors = check_method_body(
        "x = 1; switch (x) { case (1) { y = 1; } default { y = 0; } }"
    )
    assert syntax_errors(errors) == []
