"""Tests for ManuScript method body checker API.

This file tests the check_method_body() function directly.
For comprehensive error detection tests, see test/sibelius/lint/examples/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mahlif.sibelius.manuscript.checker import BUILTIN_GLOBALS
from mahlif.sibelius.manuscript.checker import check_method_body


# =============================================================================
# Module initialization tests
# =============================================================================


def test_builtin_globals_loaded() -> None:
    """Test that built-in globals are loaded from lang.json."""
    assert len(BUILTIN_GLOBALS) > 50
    assert "Sibelius" in BUILTIN_GLOBALS
    assert "True" in BUILTIN_GLOBALS
    assert "CreateSparseArray" in BUILTIN_GLOBALS


def test_missing_lang_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test error when lang.json is missing."""
    from mahlif.sibelius.manuscript import checker

    fake_path = tmp_path / "nonexistent.json"
    monkeypatch.setattr(checker, "LANG_JSON_PATH", fake_path)

    with pytest.raises(FileNotFoundError, match="Required language data file"):
        checker._load_builtin_globals()


# =============================================================================
# API tests - check_method_body parameters
# =============================================================================


def test_empty_body() -> None:
    """Test empty method body is valid."""
    errors = check_method_body("")
    assert errors == []


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
    # Currently method_name isn't used in error messages,
    # but the API accepts it for future expansion
    errors = check_method_body("x = 1;", method_name="TestMethod")
    assert errors == []


# =============================================================================
# Basic statement parsing
# =============================================================================


def test_simple_assignment() -> None:
    """Test simple assignment parses without error."""
    errors = check_method_body("x = 1;")
    assert errors == []


def test_method_call() -> None:
    """Test method call parses without error."""
    errors = check_method_body("Sibelius.MessageBox('hello');")
    assert errors == []


def test_return_statement() -> None:
    """Test return statement parses without error."""
    errors = check_method_body("return True;")
    assert errors == []


def test_multiple_statements() -> None:
    """Test multiple statements parse without error."""
    code = "x = 1; y = 2; z = x + y;"
    errors = check_method_body(code)
    assert errors == []


# =============================================================================
# Control flow - basic parsing (errors tested in lint/examples/)
# =============================================================================


def test_if_statement() -> None:
    """Test valid if statement."""
    errors = check_method_body("x = 1; if (x) { y = 1; }")
    assert errors == []


def test_while_statement() -> None:
    """Test valid while statement."""
    errors = check_method_body("x = 5; while (x > 0) { x = x - 1; }")
    assert errors == []


def test_for_statement() -> None:
    """Test valid for statement."""
    errors = check_method_body("for i = 1 to 10 { x = i; }")
    assert errors == []


def test_for_each_statement() -> None:
    """Test valid for each statement."""
    errors = check_method_body(
        "list = CreateSparseArray(); for each item in list { x = item; }"
    )
    assert errors == []


def test_for_each_with_type() -> None:
    """Test for each with type annotation."""
    errors = check_method_body("for each Note n in bar { x = n; }", parameters=["bar"])
    assert errors == []


def test_switch_statement() -> None:
    """Test valid switch statement."""
    errors = check_method_body(
        "x = 1; switch (x) { case (1) { y = 1; } default { y = 0; } }"
    )
    assert errors == []


# =============================================================================
# Expression parsing (errors tested in lint/examples/)
# =============================================================================


def test_binary_operators() -> None:
    """Test binary operators."""
    errors = check_method_body("a = 1; b = 2; x = a + b - a * b / a;")
    assert errors == []


def test_comparison_operators() -> None:
    """Test comparison operators."""
    errors = check_method_body("a = 1; b = 2; x = a < b; y = a > b; z = a = b;")
    assert errors == []


def test_logical_operators() -> None:
    """Test logical operators."""
    errors = check_method_body("a = True; b = False; x = a and b or not a;")
    assert errors == []


def test_string_concatenation() -> None:
    """Test string concatenation with &."""
    errors = check_method_body("x = 'hello' & ' ' & 'world';")
    assert errors == []


def test_unary_operators() -> None:
    """Test unary operators."""
    errors = check_method_body("x = -1; y = not True;")
    assert errors == []


def test_array_access() -> None:
    """Test array access."""
    errors = check_method_body("arr = CreateSparseArray(); x = arr[0]; arr[1] = 1;")
    assert errors == []


def test_property_access() -> None:
    """Test property access."""
    errors = check_method_body("x = Sibelius.ActiveScore;")
    assert errors == []


def test_method_call_with_args() -> None:
    """Test method call with arguments."""
    errors = check_method_body("Sibelius.MessageBox('msg', True);")
    assert errors == []


def test_chained_calls() -> None:
    """Test chained method/property access."""
    errors = check_method_body(
        "x = Sibelius.ActiveScore.NthStaff(1).FullInstrumentName;"
    )
    assert errors == []


def test_nested_parentheses() -> None:
    """Test nested parentheses."""
    errors = check_method_body("x = ((1 + 2) * (3 + 4));")
    assert errors == []


# =============================================================================
# Undefined variable detection
# =============================================================================


def test_undefined_variable_warning() -> None:
    """Test undefined variable generates warning."""
    errors = check_method_body("x = undefined_var;")
    assert any(e.code == "MS-W020" for e in errors)


def test_variable_defined_by_assignment() -> None:
    """Test variable is defined after assignment."""
    errors = check_method_body("x = 1; y = x;")
    # x is defined by first assignment, so y = x should not warn
    assert not any(e.code == "MS-W020" and "'x'" in e.message for e in errors)


def test_for_loop_variable_defined() -> None:
    """Test for loop variable is defined in body."""
    errors = check_method_body("for i = 1 to 10 { x = i; }")
    assert not any(e.code == "MS-W020" and "'i'" in e.message for e in errors)


def test_for_each_variable_defined() -> None:
    """Test for each variable is defined in body."""
    errors = check_method_body(
        "for each item in list { x = item; }", parameters=["list"]
    )
    assert not any(e.code == "MS-W020" and "'item'" in e.message for e in errors)


# =============================================================================
# Comments
# =============================================================================


def test_line_comment_skipped() -> None:
    """Test line comments are skipped."""
    errors = check_method_body("// comment\nx = 1;")
    assert errors == []


def test_inline_comment() -> None:
    """Test inline comment after statement."""
    errors = check_method_body("x = 1; // comment")
    assert errors == []


# =============================================================================
# Edge case coverage tests
# =============================================================================


def test_error_token() -> None:
    """Test that ERROR tokens from tokenizer are handled."""
    # Unterminated string creates an ERROR token
    errors = check_method_body("x = 'unterminated;")
    assert any(e.code == "MS-E030" for e in errors)  # Tokenizer error


def test_expression_with_only_semicolon() -> None:
    """Test expression that starts with just semicolon."""
    errors = check_method_body(";")
    assert errors == []  # Empty statement is valid


def test_deeply_nested_recovery() -> None:
    """Test error recovery with nested blocks."""
    # Missing closing braces should recover
    errors = check_method_body("if (x) { if (y) { z = 1; }", parameters=["x", "y", "z"])
    assert len(errors) > 0


def test_method_body_eof() -> None:
    """Test that method body ending at EOF is handled."""
    # No trailing semicolon
    errors = check_method_body("x = 1")
    assert errors == []


def test_return_without_value() -> None:
    """Test return statement without a value."""
    errors = check_method_body("return;")
    assert errors == []


def test_return_before_rbrace() -> None:
    """Test return at end of block (no semicolon before brace)."""
    errors = check_method_body("if (x) { return }", parameters=["x"])
    # Missing semicolon should generate error
    assert any(e.code == "MS-E040" for e in errors)


def test_identifier_not_followed_by_assign() -> None:
    """Test identifier followed by something other than =."""
    # x + y is an expression, not assignment
    errors = check_method_body("x + y;", parameters=["x", "y"])
    assert errors == []


def test_identifier_at_end() -> None:
    """Test identifier at end of tokens."""
    errors = check_method_body("x", parameters=["x"])
    assert errors == []


def test_recovery_to_eof() -> None:
    """Test error recovery that reaches EOF without finding brace."""
    # for without brace and no closing - recovery goes to EOF
    errors = check_method_body("for i = 1 to 5 x = i;")
    assert len(errors) > 0


def test_check_error_str() -> None:
    """Test CheckError string representation."""
    from mahlif.sibelius.manuscript.errors import CheckError

    err = CheckError(10, 5, "MS-E001", "Test error")
    assert str(err) == "10:5 [MS-E001] Test error"


def test_tokenizer_token_repr() -> None:
    """Test tokenizer Token repr."""
    from mahlif.sibelius.manuscript.tokenizer import Token, TokenType

    token = Token(TokenType.IDENTIFIER, "foo", 1, 5)
    assert "IDENTIFIER" in repr(token)
    assert "foo" in repr(token)
    assert "1:5" in repr(token)
