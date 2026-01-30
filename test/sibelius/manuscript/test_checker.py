"""Tests for ManuScript method body checker API.

This file tests the check_method_body() function directly.
For comprehensive error detection tests, see test/sibelius/lint/examples/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mahlif.sibelius.manuscript.checker import BUILTIN_GLOBALS
from mahlif.sibelius.manuscript.checker import check_method_body
from mahlif.sibelius.manuscript.errors import LintError


def syntax_errors(errors: list[LintError]) -> list[LintError]:
    """Filter to only syntax errors, excluding semantic warnings."""
    # Filter out warnings that are noisy for simple test snippets
    excluded = {"MS-W025", "MS-W030", "MS-W033"}  # unused var, empty stmt, shadowing
    return [e for e in errors if e.code not in excluded]


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
    # Currently method_name isn't used in error messages,
    # but the API accepts it for future expansion
    errors = check_method_body("x = 1;", method_name="TestMethod")
    assert syntax_errors(errors) == []


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
# Control flow - basic parsing (errors tested in lint/examples/)
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


# =============================================================================
# Expression parsing (errors tested in lint/examples/)
# =============================================================================


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
    assert syntax_errors(errors) == []


def test_inline_comment() -> None:
    """Test inline comment after statement."""
    errors = check_method_body("x = 1; // comment")
    assert syntax_errors(errors) == []


# =============================================================================
# Edge case coverage tests
# =============================================================================


def test_error_token() -> None:
    """Test that ERROR tokens from tokenizer are handled."""
    # Unterminated string creates an ERROR token
    errors = check_method_body("x = 'unterminated;")
    assert any(e.code == "MS-E030" for e in errors)  # Tokenizer error


def test_expression_with_only_semicolon() -> None:
    """Test expression that starts with just semicolon - warns but no syntax error."""
    errors = check_method_body(";")
    # No syntax errors, but MS-W030 warning
    assert syntax_errors(errors) == []
    assert any(e.code == "MS-W030" for e in errors)


def test_deeply_nested_recovery() -> None:
    """Test error recovery with nested blocks."""
    # Missing closing braces should recover
    errors = check_method_body("if (x) { if (y) { z = 1; }", parameters=["x", "y", "z"])
    assert len(errors) > 0


def test_method_body_eof() -> None:
    """Test that method body ending at EOF is handled."""
    # No trailing semicolon
    errors = check_method_body("x = 1")
    assert syntax_errors(errors) == []


def test_return_without_value() -> None:
    """Test return statement without a value."""
    errors = check_method_body("return;")
    assert syntax_errors(errors) == []


def test_return_before_rbrace() -> None:
    """Test return at end of block (no semicolon before brace)."""
    errors = check_method_body("if (x) { return }", parameters=["x"])
    # Missing semicolon should generate error
    assert any(e.code == "MS-E040" for e in errors)


def test_identifier_not_followed_by_assign() -> None:
    """Test identifier followed by something other than =."""
    # x + y is an expression, not assignment
    errors = check_method_body("x + y;", parameters=["x", "y"])
    assert syntax_errors(errors) == []


def test_identifier_at_end() -> None:
    """Test identifier at end of tokens."""
    errors = check_method_body("x", parameters=["x"])
    assert syntax_errors(errors) == []


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
    assert syntax_errors(errors) == []


def test_gte_operator() -> None:
    """Test greater-than-or-equal operator."""
    errors = check_method_body("if (x >= 5) { y = 1; }", parameters=["x", "y"])
    assert syntax_errors(errors) == []


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
    assert syntax_errors(errors) == []


def test_two_char_operator_at_end() -> None:
    """Test two-character operator at end of source."""
    # This tests _advance(2) when close to end of source
    errors = check_method_body("x <= y", parameters=["x", "y"])
    assert syntax_errors(errors) == []


def test_neq_operator() -> None:
    """Test != operator."""
    errors = check_method_body("if (x != y) { z = 1; }", parameters=["x", "y", "z"])
    assert syntax_errors(errors) == []


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
    assert syntax_errors(errors) == []


def test_valid_builtin_function() -> None:
    """Test no warning for valid builtin function."""
    errors = check_method_body("x = Chr(65);")
    assert syntax_errors(errors) == []


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
    assert syntax_errors(errors) == []


def test_chained_property_then_method() -> None:
    """Test chained access doesn't false-positive."""
    # Sibelius.ActiveScore is property access, then .NthStaff is method on unknown
    errors = check_method_body("x = Sibelius.ActiveScore.NthStaff(1);")
    assert syntax_errors(errors) == []


def test_direct_method_call() -> None:
    """Test direct Sibelius.Method() is checked."""
    errors = check_method_body("Sibelius.MessageBox(msg);", parameters=["msg"])
    assert syntax_errors(errors) == []

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
    assert syntax_errors(errors) == []


def test_unknown_without_plugin_methods() -> None:
    """Test warning when plugin method is not passed."""
    errors = check_method_body(
        "result = ProcessBar(bar);",
        parameters=["bar"],
        # No plugin_methods passed - should warn
    )
    w022_errors = [e for e in errors if e.code == "MS-W022"]
    assert len(w022_errors) == 1


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


# =============================================================================
# MS-W023: Argument count validation
# =============================================================================


def test_arg_count_correct() -> None:
    """Test no warning when argument count is correct."""
    errors = check_method_body("x = Chr(65);")
    w023_errors = [e for e in errors if e.code == "MS-W023"]
    assert w023_errors == []


def test_arg_count_too_few() -> None:
    """Test warning when too few arguments."""
    errors = check_method_body("x = Chr();")
    assert any(e.code == "MS-W023" and "got 0" in e.message for e in errors)


def test_arg_count_too_many() -> None:
    """Test warning when too many arguments."""
    errors = check_method_body("x = Chr(65, 66);")
    assert any(e.code == "MS-W023" and "got 2" in e.message for e in errors)


def test_arg_count_method_too_few() -> None:
    """Test warning on method with too few arguments."""
    errors = check_method_body("Sibelius.CreateTextFile();")
    assert any(e.code == "MS-W023" for e in errors)


def test_arg_count_optional_params() -> None:
    """Test optional parameters allow variable arg counts."""
    # Substring with all 3 args - should be valid
    errors = check_method_body("x = Substring('hello', 0, 5);")
    w023_errors = [e for e in errors if e.code == "MS-W023"]
    assert w023_errors == []


# =============================================================================
# MS-W024: Undefined property detection
# =============================================================================


def test_property_valid() -> None:
    """Test no warning for valid property."""
    errors = check_method_body("x = Sibelius.ActiveScore;")
    w024_errors = [e for e in errors if e.code == "MS-W024"]
    assert w024_errors == []


def test_property_invalid_with_suggestion() -> None:
    """Test warning with 'did you mean' suggestion."""
    errors = check_method_body("x = Sibelius.ActiveScor;")
    assert any(
        e.code == "MS-W024"
        and "did you mean" in e.message
        and "ActiveScore" in e.message
        for e in errors
    )


def test_property_invalid_no_suggestion() -> None:
    """Test warning without suggestion for very different name."""
    errors = check_method_body("x = Sibelius.Xyz123;")
    assert any(e.code == "MS-W024" and "did you mean" not in e.message for e in errors)


def test_property_case_mismatch() -> None:
    """Test suggestion for case mismatch."""
    errors = check_method_body("x = Sibelius.activescore;")
    assert any(e.code == "MS-W024" and "ActiveScore" in e.message for e in errors)


# =============================================================================
# MS-W025: Unused variable detection
# =============================================================================


def test_unused_variable_warning() -> None:
    """Test warning for unused variable."""
    errors = check_method_body("x = 1;")
    assert any(e.code == "MS-W025" and "x" in e.message for e in errors)


def test_used_variable_no_warning() -> None:
    """Test no warning when variable is used."""
    errors = check_method_body("x = 1; y = x;")
    w025_errors = [e for e in errors if e.code == "MS-W025"]
    # x is used, y is not
    assert not any("'x'" in e.message for e in w025_errors)
    assert any("'y'" in e.message for e in w025_errors)


def test_parameter_not_unused() -> None:
    """Test parameters are not flagged as unused."""
    errors = check_method_body("y = 1;", parameters=["x"])
    w025_errors = [e for e in errors if e.code == "MS-W025"]
    # x is a parameter, should not be warned
    assert not any("'x'" in e.message for e in w025_errors)
    # y is unused
    assert any("'y'" in e.message for e in w025_errors)


def test_loop_variable_not_unused() -> None:
    """Test loop variables are not flagged as unused."""
    errors = check_method_body("for i = 0 to 10 { }")
    w025_errors = [e for e in errors if e.code == "MS-W025"]
    # i is a loop variable, should not be warned
    assert not any("'i'" in e.message for e in w025_errors)


# =============================================================================
# MS-W026: Unreachable code detection
# =============================================================================


def test_unreachable_code_after_return() -> None:
    """Test warning for code after return."""
    errors = check_method_body("return 1; x = 2;")
    assert any(e.code == "MS-W026" for e in errors)


def test_no_unreachable_return_at_end() -> None:
    """Test no warning when return is at end."""
    errors = check_method_body("x = 1; return x;")
    w026_errors = [e for e in errors if e.code == "MS-W026"]
    assert w026_errors == []


def test_return_in_if_block_ok() -> None:
    """Test code after if block with return is not unreachable."""
    errors = check_method_body("if (True) { return 1; } x = 2;")
    w026_errors = [e for e in errors if e.code == "MS-W026"]
    assert w026_errors == []


# =============================================================================
# MS-W028: Constant condition in if
# =============================================================================


def test_constant_condition_true() -> None:
    """Test warning for if (True) with dead else message."""
    errors = check_method_body("if (True) { }")
    assert any(e.code == "MS-W028" and "always true" in e.message for e in errors)


def test_constant_condition_false() -> None:
    """Test warning for if (False) with dead body message."""
    errors = check_method_body("if (False) { }")
    assert any(e.code == "MS-W028" and "always false" in e.message for e in errors)


def test_constant_condition_number() -> None:
    """Test warning for if (0)."""
    errors = check_method_body("if (0) { }")
    assert any(e.code == "MS-W028" for e in errors)


def test_while_constant_ok() -> None:
    """Test no warning for while (True) - common pattern."""
    errors = check_method_body("while (True) { break; }")
    w028_errors = [e for e in errors if e.code == "MS-W028"]
    assert w028_errors == []


# =============================================================================
# MS-W029: Self-assignment detection
# =============================================================================


def test_self_assignment_warning() -> None:
    """Test warning for x = x."""
    errors = check_method_body("x = x;", parameters=["x"])
    assert any(e.code == "MS-W029" for e in errors)


def test_normal_assignment_no_warning() -> None:
    """Test no warning for normal assignment."""
    errors = check_method_body("x = y;", parameters=["x", "y"])
    w029_errors = [e for e in errors if e.code == "MS-W029"]
    assert w029_errors == []


def test_self_with_expression_no_warning() -> None:
    """Test no warning for x = x + 1."""
    errors = check_method_body("x = x + 1;", parameters=["x"])
    w029_errors = [e for e in errors if e.code == "MS-W029"]
    assert w029_errors == []


# =============================================================================
# MS-W030: Empty statement detection
# =============================================================================


def test_empty_statement_warning() -> None:
    """Test warning for lone semicolon."""
    errors = check_method_body(";;")
    assert len([e for e in errors if e.code == "MS-W030"]) == 2


def test_normal_statement_no_empty_warning() -> None:
    """Test no warning for normal statement."""
    errors = check_method_body("return 1;")
    w030_errors = [e for e in errors if e.code == "MS-W030"]
    assert w030_errors == []


# =============================================================================
# MS-W031: Division/modulo by zero
# =============================================================================


def test_division_by_zero() -> None:
    """Test warning for x / 0."""
    errors = check_method_body("x = 10 / 0;", parameters=["x"])
    assert any(e.code == "MS-W031" and "Division" in e.message for e in errors)


def test_modulo_by_zero() -> None:
    """Test warning for x % 0."""
    errors = check_method_body("x = 10 % 0;", parameters=["x"])
    assert any(e.code == "MS-W031" and "Modulo" in e.message for e in errors)


def test_division_by_nonzero_ok() -> None:
    """Test no warning for x / 2."""
    errors = check_method_body("x = 10 / 2;", parameters=["x"])
    w031_errors = [e for e in errors if e.code == "MS-W031"]
    assert w031_errors == []


# =============================================================================
# MS-W032: Comparison to self
# =============================================================================


def test_comparison_to_self_equal() -> None:
    """Test warning for x = x (always true)."""
    errors = check_method_body("if (x = x) { }", parameters=["x"])
    assert any(e.code == "MS-W032" and "always true" in e.message for e in errors)


def test_comparison_to_self_not_equal() -> None:
    """Test warning for x != x (always false)."""
    errors = check_method_body("if (x != x) { }", parameters=["x"])
    assert any(e.code == "MS-W032" and "always false" in e.message for e in errors)


def test_comparison_different_vars_ok() -> None:
    """Test no warning for x = y."""
    errors = check_method_body("if (x = y) { }", parameters=["x", "y"])
    w032_errors = [e for e in errors if e.code == "MS-W032"]
    assert w032_errors == []


# =============================================================================
# MS-W033: Variable shadowing
# =============================================================================


def test_variable_shadows_parameter() -> None:
    """Test warning when local shadows parameter."""
    errors = check_method_body("x = 1;", parameters=["x"])
    assert any(e.code == "MS-W033" and "shadows" in e.message for e in errors)


def test_new_variable_no_shadow() -> None:
    """Test no warning for new variable."""
    errors = check_method_body("y = 1;", parameters=["x"])
    w033_errors = [e for e in errors if e.code == "MS-W033"]
    assert w033_errors == []
