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
        checker._load_lang_data()


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


def test_lte_operator() -> None:
    """Test less-than-or-equal operator."""
    errors = check_method_body("if (x <= 5) { y = 1; }", parameters=["x", "y"])
    assert errors == []


def test_gte_operator() -> None:
    """Test greater-than-or-equal operator."""
    errors = check_method_body("if (x >= 5) { y = 1; }", parameters=["x", "y"])
    assert errors == []


def test_unknown_character() -> None:
    """Test that unknown characters generate errors."""
    # Backtick is not valid in ManuScript
    errors = check_method_body("x = `test`;", parameters=["x"])
    assert any(e.code == "MS-E031" for e in errors)


def test_string_with_newline() -> None:
    """Test unterminated string at newline."""
    # String with embedded newline - should error
    errors = check_method_body("x = 'hello\nworld';", parameters=["x"])
    assert any(e.code == "MS-E030" for e in errors)


def test_multiline_code() -> None:
    """Test code with newlines exercises newline handling."""
    code = """x = 1;
y = 2;
z = x + y;"""
    errors = check_method_body(code, parameters=["x", "y", "z"])
    assert errors == []


def test_two_char_operator_at_end() -> None:
    """Test two-character operator at end of source."""
    # This tests _advance(2) when close to end of source
    errors = check_method_body("x <= y", parameters=["x", "y"])
    assert errors == []


def test_neq_operator() -> None:
    """Test != operator."""
    errors = check_method_body("if (x != y) { z = 1; }", parameters=["x", "y", "z"])
    assert errors == []


def test_operator_at_very_end() -> None:
    """Test operator at very end of source (no trailing content)."""
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    # When tokenizing "x<=", _advance(2) is called at pos=1 (length=3)
    # First iteration advances to pos=2, second advances to pos=3 which equals len
    # This tests the boundary condition in _advance
    tokenizer = MethodBodyTokenizer("x<=")
    tokens = list(tokenizer.tokenize())
    assert any(t.type.name == "LTE" for t in tokens)


def test_unterminated_string_with_escape_at_end() -> None:
    """Test unterminated string ending with escape sequence.

    This exercises the _advance(2) boundary condition when the escape
    is at the very end of the source.
    """
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    # 'a\ - escape at end with no char to escape
    tokenizer = MethodBodyTokenizer("'a\\")
    tokens = list(tokenizer.tokenize())
    # Should get ERROR token for unterminated string
    assert any(t.type.name == "ERROR" for t in tokens)
    assert any(e.code == "MS-E030" for e in tokenizer.errors)


# =============================================================================
# MS-W022: Undefined function/method detection
# =============================================================================


def test_undefined_method_on_sibelius() -> None:
    """Test warning for undefined method on Sibelius object."""
    errors = check_method_body("Sibelius.WriteTextFile(path);", parameters=["path"])
    assert len(errors) == 1
    assert errors[0].code == "MS-W022"
    assert "WriteTextFile" in errors[0].message
    assert "Sibelius" in errors[0].message


def test_valid_method_on_sibelius() -> None:
    """Test no warning for valid Sibelius method."""
    errors = check_method_body("Sibelius.CreateTextFile(path);", parameters=["path"])
    assert errors == []


def test_valid_builtin_function() -> None:
    """Test no warning for valid builtin function."""
    errors = check_method_body("x = Chr(65);")
    assert errors == []


def test_undefined_bare_function() -> None:
    """Test warning for completely unknown function."""
    errors = check_method_body("FooBarBaz123();")
    assert len(errors) == 1
    assert errors[0].code == "MS-W022"
    assert "FooBarBaz123" in errors[0].message


def test_method_exists_on_other_object() -> None:
    """Test no warning when method exists on some object (could be valid)."""
    # NthBar exists on Score, Staff, etc.
    errors = check_method_body("x.NthBar(1);", parameters=["x"])
    assert errors == []


def test_chained_property_then_method() -> None:
    """Test chained access doesn't false-positive."""
    # Sibelius.ActiveScore is property access, then .NthStaff is method on unknown
    errors = check_method_body("x = Sibelius.ActiveScore.NthStaff(1);")
    assert errors == []


def test_direct_method_call() -> None:
    """Test direct Sibelius.Method() is checked."""
    errors = check_method_body("Sibelius.MessageBox(msg);", parameters=["msg"])
    assert errors == []

    errors = check_method_body("Sibelius.NoSuchMethod(msg);", parameters=["msg"])
    assert len(errors) == 1
    assert errors[0].code == "MS-W022"


def test_plugin_method_call() -> None:
    """Test no warning when calling a plugin's own method."""
    errors = check_method_body(
        "result = ProcessBar(bar);",
        parameters=["bar"],
        plugin_methods={"ProcessBar", "Initialize", "Run"},
    )
    assert errors == []


def test_unknown_without_plugin_methods() -> None:
    """Test warning when plugin method is not passed."""
    errors = check_method_body(
        "result = ProcessBar(bar);",
        parameters=["bar"],
        # No plugin_methods passed - should warn
    )
    assert len(errors) == 1
    assert errors[0].code == "MS-W022"


def test_object_name_as_function() -> None:
    """Test that using object type name as function doesn't warn."""
    # ManuScript doesn't have constructors, but we allow this pattern
    errors = check_method_body("x = Sibelius();")
    # Should not warn - Sibelius is a known object type
    w022_errors = [e for e in errors if e.code == "MS-W022"]
    assert w022_errors == []


def test_call_method_on_any_object() -> None:
    """Test that methods existing on ANY object don't warn when receiver unknown."""
    # NthBar exists on Staff, Score, etc. - should be allowed on unknown receiver
    errors = check_method_body("x = unknown.NthBar(1);", parameters=["unknown"])
    w022_errors = [e for e in errors if e.code == "MS-W022"]
    assert w022_errors == []
