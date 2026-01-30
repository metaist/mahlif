"""Tests for expression parsing in checker."""

from __future__ import annotations

from mahlif.sibelius.manuscript.checker import check_method_body
from mahlif.sibelius.manuscript.errors import LintError


def syntax_errors(errors: list[LintError]) -> list[LintError]:
    """Filter to only syntax errors, excluding semantic warnings."""
    excluded = {"MS-W025", "MS-W030", "MS-W033"}
    return [e for e in errors if e.code not in excluded]


def test_binary_operators() -> None:
    """Test binary operators."""
    errors = check_method_body("a = 1; b = 2; x = a + b - a * b / a;")
    assert syntax_errors(errors) == []


def test_comparison_operators() -> None:
    """Test comparison operators."""
    errors = check_method_body("a = 1; b = 2; x = a < b; y = a > b; z = a = b;")
    assert syntax_errors(errors) == []


def test_logical_operators() -> None:
    """Test logical operators."""
    errors = check_method_body("a = True; b = False; x = a and b or not a;")
    assert syntax_errors(errors) == []


def test_string_concatenation() -> None:
    """Test string concatenation with &."""
    errors = check_method_body("x = 'hello' & ' ' & 'world';")
    assert syntax_errors(errors) == []


def test_unary_operators() -> None:
    """Test unary operators."""
    errors = check_method_body("x = -1; y = not True;")
    assert syntax_errors(errors) == []


def test_array_access() -> None:
    """Test array access."""
    errors = check_method_body("arr = CreateSparseArray(); x = arr[0]; arr[1] = 1;")
    assert syntax_errors(errors) == []


def test_property_access() -> None:
    """Test property access."""
    errors = check_method_body("x = Sibelius.ActiveScore;")
    assert syntax_errors(errors) == []


def test_method_call_with_args() -> None:
    """Test method call with arguments."""
    errors = check_method_body("Sibelius.MessageBox('msg');")
    assert syntax_errors(errors) == []


def test_chained_calls() -> None:
    """Test chained method/property access."""
    errors = check_method_body(
        "x = Sibelius.ActiveScore.NthStaff(1).FullInstrumentName;"
    )
    assert syntax_errors(errors) == []


def test_nested_parentheses() -> None:
    """Test nested parentheses."""
    errors = check_method_body("x = ((1 + 2) * (3 + 4));")
    assert syntax_errors(errors) == []


def test_lte_operator() -> None:
    """Test less-than-or-equal operator."""
    errors = check_method_body("if (x <= 5) { y = 1; }", parameters=["x", "y"])
    assert syntax_errors(errors) == []


def test_gte_operator() -> None:
    """Test greater-than-or-equal operator."""
    errors = check_method_body("if (x >= 5) { y = 1; }", parameters=["x", "y"])
    assert syntax_errors(errors) == []


def test_neq_operator() -> None:
    """Test != operator."""
    errors = check_method_body("if (x != y) { z = 1; }", parameters=["x", "y", "z"])
    assert syntax_errors(errors) == []


def test_two_char_operator_at_end() -> None:
    """Test two-character operator at end of source."""
    errors = check_method_body("x <= y", parameters=["x", "y"])
    assert syntax_errors(errors) == []


def test_operator_at_very_end() -> None:
    """Test operator at very end of source (no trailing content)."""
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    tokenizer = MethodBodyTokenizer("x<=")
    tokens = list(tokenizer.tokenize())
    assert any(t.type.name == "LTE" for t in tokens)
