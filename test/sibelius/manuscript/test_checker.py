"""Tests for ManuScript method body checker."""

from __future__ import annotations

from mahlif.sibelius.manuscript.checker import BUILTIN_GLOBALS
from mahlif.sibelius.manuscript.checker import check_method_body


# =============================================================================
# BUILTIN_GLOBALS tests
# =============================================================================


def test_builtin_globals_loaded() -> None:
    """Test that built-in globals are loaded from lang.json."""
    assert len(BUILTIN_GLOBALS) > 50
    assert "Sibelius" in BUILTIN_GLOBALS
    assert "True" in BUILTIN_GLOBALS
    assert "CreateSparseArray" in BUILTIN_GLOBALS


# =============================================================================
# Basic statement tests
# =============================================================================


def test_empty_body() -> None:
    """Test empty method body."""
    errors = check_method_body("")
    assert errors == []


def test_simple_assignment() -> None:
    """Test simple assignment."""
    errors = check_method_body("x = 1;", parameters=VARS)
    assert errors == []


def test_method_call() -> None:
    """Test method call."""
    errors = check_method_body("Sibelius.MessageBox('hello');")
    assert errors == []


def test_return_statement() -> None:
    """Test return statement."""
    errors = check_method_body("return True;")
    assert errors == []


def test_empty_statement() -> None:
    """Test empty statement (just semicolon)."""
    errors = check_method_body(";")
    assert errors == []


# Helper to avoid undefined variable warnings in tests
VARS = [
    "x",
    "y",
    "z",
    "a",
    "b",
    "c",
    "d",
    "e",
    "i",
    "j",
    "n",
    "item",
    "list",
    "arr",
    "obj",
    "score",
    "bar",
]


# =============================================================================
# Control flow - if statement
# =============================================================================


def test_if_statement() -> None:
    """Test valid if statement."""
    errors = check_method_body("if (x) { y = 1; }", parameters=VARS)
    assert errors == []


def test_if_else_statement() -> None:
    """Test valid if-else statement."""
    errors = check_method_body("if (x) { y = 1; } else { y = 2; }", parameters=VARS)
    assert errors == []


def test_if_missing_lparen() -> None:
    """Test if without opening paren."""
    errors = check_method_body("if x) { y = 1; }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_if_missing_rparen() -> None:
    """Test if without closing paren."""
    errors = check_method_body("if (x { y = 1; }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_if_missing_brace() -> None:
    """Test if without opening brace."""
    errors = check_method_body("if (x) y = 1;", parameters=VARS)
    assert any(e.code == "MS-E043" for e in errors)  # Missing brace


# =============================================================================
# Control flow - while statement
# =============================================================================


def test_while_statement() -> None:
    """Test valid while statement."""
    errors = check_method_body("while (x) { x = x - 1; }", parameters=VARS)
    assert errors == []


def test_while_missing_lparen() -> None:
    """Test while without opening paren."""
    errors = check_method_body("while x) { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_while_missing_rparen() -> None:
    """Test while without closing paren."""
    errors = check_method_body("while (x { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_while_missing_brace() -> None:
    """Test while without opening brace."""
    errors = check_method_body("while (x) x = 1;", parameters=VARS)
    assert any(e.code == "MS-E043" for e in errors)  # Missing brace


# =============================================================================
# Control flow - for statement
# =============================================================================


def test_for_statement() -> None:
    """Test valid for statement."""
    errors = check_method_body("for i = 1 to 10 { x = i; }", parameters=VARS)
    assert errors == []


def test_for_missing_equals() -> None:
    """Test for without = after variable."""
    errors = check_method_body("for i 1 to 10 { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_for_missing_to() -> None:
    """Test for without 'to' keyword."""
    errors = check_method_body("for i = 1 10 { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_for_missing_brace() -> None:
    """Test for without opening brace."""
    errors = check_method_body("for i = 1 to 10 x = i;", parameters=VARS)
    assert any(e.code == "MS-E043" for e in errors)  # Missing brace


def test_for_missing_identifier() -> None:
    """Test for without loop variable."""
    errors = check_method_body("for 1 = 1 to 10 { }")
    assert any(e.code == "MS-E041" for e in errors)  # For syntax error


# =============================================================================
# Control flow - for each statement
# =============================================================================


def test_for_each_statement() -> None:
    """Test valid for each statement."""
    errors = check_method_body("for each item in list { x = item; }", parameters=VARS)
    assert errors == []


def test_for_each_with_type() -> None:
    """Test for each with type annotation."""
    errors = check_method_body("for each Note n in bar { x = n; }", parameters=VARS)
    assert errors == []


def test_for_each_missing_in() -> None:
    """Test for each without 'in' keyword."""
    errors = check_method_body("for each item list { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)  # Expected 'in'


def test_for_each_missing_variable() -> None:
    """Test for each without loop variable."""
    errors = check_method_body("for each in list { }", parameters=VARS)
    assert any(e.code == "MS-E041" for e in errors)


def test_for_each_missing_brace() -> None:
    """Test for each without opening brace."""
    errors = check_method_body("for each item in list x = item;", parameters=VARS)
    assert any(e.code == "MS-E043" for e in errors)  # Missing brace


# =============================================================================
# Control flow - switch statement
# =============================================================================


def test_switch_statement() -> None:
    """Test valid switch statement."""
    errors = check_method_body("switch (x) { case (1) { y = 1; } }", parameters=VARS)
    assert errors == []


def test_switch_with_default() -> None:
    """Test switch with default case."""
    errors = check_method_body(
        "switch (x) { case (1) { y = 1; } default { y = 0; } }", parameters=VARS
    )
    assert errors == []


def test_switch_missing_lparen() -> None:
    """Test switch without opening paren."""
    errors = check_method_body("switch x) { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_switch_missing_rparen() -> None:
    """Test switch without closing paren."""
    errors = check_method_body("switch (x { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_switch_case_missing_lparen() -> None:
    """Test case without opening paren."""
    errors = check_method_body("switch (x) { case 1) { } }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_switch_case_missing_rparen() -> None:
    """Test case without closing paren."""
    errors = check_method_body("switch (x) { case (1 { } }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)


def test_switch_case_missing_brace() -> None:
    """Test case without opening brace."""
    errors = check_method_body("switch (x) { case (1) y = 1; }", parameters=VARS)
    assert any(e.code == "MS-E043" for e in errors)  # Missing brace


# =============================================================================
# Expression tests
# =============================================================================


def test_binary_expression() -> None:
    """Test binary expressions."""
    errors = check_method_body("x = 1 + 2;", parameters=VARS)
    assert errors == []


def test_comparison_expression() -> None:
    """Test comparison expressions."""
    errors = check_method_body("x = a > b;", parameters=VARS)
    assert errors == []


def test_logical_expression() -> None:
    """Test logical expressions."""
    errors = check_method_body("x = a and b or c;", parameters=VARS)
    assert errors == []


def test_unary_not() -> None:
    """Test unary not expression."""
    errors = check_method_body("x = not y;", parameters=VARS)
    assert errors == []


def test_unary_minus() -> None:
    """Test unary minus expression."""
    errors = check_method_body("x = -1;", parameters=VARS)
    assert errors == []


def test_parenthesized_expression() -> None:
    """Test parenthesized expression."""
    errors = check_method_body("x = (1 + 2) * 3;", parameters=VARS)
    assert errors == []


def test_array_access() -> None:
    """Test array access."""
    errors = check_method_body("x = arr[0];", parameters=VARS)
    assert errors == []


def test_property_access() -> None:
    """Test property access."""
    errors = check_method_body("x = obj.Property;", parameters=VARS)
    assert errors == []


def test_method_call_with_args() -> None:
    """Test method call with arguments."""
    errors = check_method_body("x = obj.Method(1, 2, 3);", parameters=VARS)
    assert errors == []


def test_string_concatenation() -> None:
    """Test string concatenation with &."""
    errors = check_method_body("x = 'a' & 'b';", parameters=VARS)
    assert errors == []


def test_empty_expression() -> None:
    """Test empty expression after =."""
    errors = check_method_body("x = ;", parameters=VARS)
    assert any(e.code == "MS-E048" for e in errors)  # Unexpected token


def test_incomplete_binary() -> None:
    """Test incomplete binary expression."""
    errors = check_method_body("x = 1 +;", parameters=VARS)
    assert any(e.code == "MS-E046" for e in errors)


def test_unclosed_paren() -> None:
    """Test unclosed parenthesis."""
    errors = check_method_body("x = (1 + 2;", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)  # Expected token


def test_missing_property_name() -> None:
    """Test missing property name after dot."""
    errors = check_method_body("x = obj.;", parameters=VARS)
    assert any(e.code == "MS-E047" for e in errors)  # Expected property name


def test_unclosed_bracket() -> None:
    """Test unclosed bracket."""
    errors = check_method_body("x = arr[0;", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)  # Expected token


def test_unclosed_function_call() -> None:
    """Test unclosed function call."""
    errors = check_method_body("x = func(1, 2;", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)  # Expected token


# =============================================================================
# Undefined variable tests
# =============================================================================


def test_undefined_variable() -> None:
    """Test undefined variable warning."""
    errors = check_method_body("x = undefined_var;")
    assert any(e.code == "MS-W020" for e in errors)


def test_defined_by_assignment() -> None:
    """Test variable defined by assignment."""
    errors = check_method_body("x = 1; y = x;", parameters=VARS)
    # No warning for x since it was assigned
    assert not any(e.code == "MS-W020" and "x" in e.message for e in errors)


def test_parameter_defined() -> None:
    """Test parameter is considered defined."""
    errors = check_method_body("y = a + b;", parameters=["a", "b"])
    assert not any(e.code == "MS-W020" for e in errors)


def test_builtin_defined() -> None:
    """Test built-in is considered defined."""
    errors = check_method_body("x = Sibelius.ActiveScore;", parameters=VARS)
    assert not any(e.code == "MS-W020" and "Sibelius" in e.message for e in errors)


def test_for_loop_variable_defined() -> None:
    """Test for loop variable is defined in body."""
    errors = check_method_body("for i = 1 to 10 { x = i; }", parameters=VARS)
    assert not any(e.code == "MS-W020" and "'i'" in e.message for e in errors)


def test_for_each_variable_defined() -> None:
    """Test for each variable is defined in body."""
    errors = check_method_body("for each item in list { x = item; }", parameters=VARS)
    assert not any(e.code == "MS-W020" and "'item'" in e.message for e in errors)


def test_global_vars_defined() -> None:
    """Test global vars passed to checker are defined."""
    errors = check_method_body("x = GlobalVar;", global_vars={"GlobalVar"})
    assert not any(e.code == "MS-W020" for e in errors)


# =============================================================================
# Edge cases
# =============================================================================


def test_nested_blocks() -> None:
    """Test deeply nested blocks."""
    errors = check_method_body(
        "if (a) { if (b) { if (c) { x = 1; } } }", parameters=VARS
    )
    assert errors == []


def test_complex_expression() -> None:
    """Test complex expression."""
    errors = check_method_body("x = (a + b) * (c - d) / e;", parameters=VARS)
    assert errors == []


def test_chained_method_calls() -> None:
    """Test chained method calls."""
    errors = check_method_body("x = obj.Method1().Method2().Property;", parameters=VARS)
    assert errors == []


def test_array_in_array() -> None:
    """Test nested array access."""
    errors = check_method_body("x = arr[i][j];", parameters=VARS)
    assert errors == []


def test_comment_skipped() -> None:
    """Test that comments are skipped."""
    errors = check_method_body("// comment\nx = 1;")
    assert errors == []


def test_block_comment_not_supported() -> None:
    """Block comments are not supported in method bodies (line comments are)."""
    # This is a known limitation - use // comments instead
    errors = check_method_body("/* comment */ x = 1;", parameters=VARS)
    # Should have errors because /* isn't recognized
    assert len(errors) > 0


def test_line_col_offset() -> None:
    """Test that line/col offsets are applied."""
    errors = check_method_body(
        "x = undefined_var;", start_line=10, start_col=5, parameters=VARS
    )
    assert errors[0].line >= 10


def test_standalone_block() -> None:
    """Test standalone block (naked braces)."""
    errors = check_method_body("{ x = 1; }", parameters=VARS)
    assert errors == []


def test_return_with_expression() -> None:
    """Test return with expression."""
    errors = check_method_body("return x + 1;", parameters=VARS)
    assert errors == []


def test_return_without_expression() -> None:
    """Test return without expression (return;)."""
    errors = check_method_body("return;")
    assert errors == []


# =============================================================================
# Tokenizer edge cases (via checker)
# =============================================================================


def test_number_formats() -> None:
    """Test various number formats."""
    errors = check_method_body("x = 123; y = 0; z = -42;", parameters=VARS)
    assert errors == []


def test_string_with_escapes() -> None:
    """Test string with escape sequences."""
    errors = check_method_body(r"x = 'it\'s';", parameters=VARS)
    assert errors == []


def test_double_quoted_string() -> None:
    """Test double-quoted string."""
    errors = check_method_body('x = "hello";', parameters=VARS)
    assert errors == []


def test_comparison_operators() -> None:
    """Test all comparison operators."""
    errors = check_method_body(
        "a = x < y; b = x > y; c = x <= y; d = x >= y; e = x = y; f = x != y;",
        parameters=VARS,
    )
    assert errors == []


def test_equals_vs_assign() -> None:
    """Test = used for both assignment and comparison."""
    # In ManuScript, = is both assignment and equality
    errors = check_method_body("if (x = 1) { y = 2; }", parameters=VARS)
    assert errors == []


# =============================================================================
# Additional coverage tests
# =============================================================================


def test_for_each_type_missing_in() -> None:
    """Test for each with type but missing 'in'."""
    # This covers the "type var" branch when 'in' is missing
    errors = check_method_body("for each Note n score { }", parameters=VARS)
    assert any(e.code == "MS-E040" for e in errors)  # Expected 'in'


def test_expression_starts_with_semicolon() -> None:
    """Test expression that starts with semicolon."""
    # Triggers MS-E045 "Expected expression" branch
    errors = check_method_body("if (x) { ; }", parameters=VARS)
    # The semicolon is an empty statement, which is valid
    assert errors == []


def test_expression_starts_with_comma() -> None:
    """Test expression statement starting with comma (invalid)."""
    errors = check_method_body(", x;", parameters=VARS)
    assert any(e.code == "MS-E045" for e in errors)


def test_empty_assignment_rparen() -> None:
    """Test empty right side after = ending with )."""
    errors = check_method_body("x = )", parameters=VARS)
    assert any(e.code in ("MS-E045", "MS-E048") for e in errors)


def test_for_each_no_identifier_at_all() -> None:
    """Test for each with 'in' as first token after 'each'."""
    errors = check_method_body("for each in { }", parameters=VARS)
    assert any(e.code == "MS-E041" for e in errors)


def test_deeply_nested_parens() -> None:
    """Test deeply nested parentheses."""
    errors = check_method_body("x = (((1 + 2)));", parameters=VARS)
    assert errors == []


def test_multiple_statements() -> None:
    """Test multiple statements in sequence."""
    code = """
    x = 1;
    y = 2;
    z = x + y;
    return z;
    """
    errors = check_method_body(code, parameters=VARS)
    assert errors == []


def test_switch_multiple_cases() -> None:
    """Test switch with multiple cases."""
    code = """
    switch (x) {
        case (1) { y = 1; }
        case (2) { y = 2; }
        case (3) { y = 3; }
        default { y = 0; }
    }
    """
    errors = check_method_body(code, parameters=VARS)
    assert errors == []


def test_for_each_with_type_variable() -> None:
    """Test for each with explicit type (Note, Bar, etc.)."""
    # "for each Note n in bar" pattern
    errors = check_method_body("for each Note n in bar { x = n; }", parameters=VARS)
    assert errors == []


def test_empty_parameter_list() -> None:
    """Test with empty parameters list."""
    errors = check_method_body("x = 1;", parameters=[])
    assert errors == []


def test_method_call_no_args() -> None:
    """Test method call with no arguments."""
    errors = check_method_body("x = obj.Method();", parameters=VARS)
    assert errors == []


def test_array_assignment() -> None:
    """Test array element assignment."""
    errors = check_method_body("arr[0] = 1;", parameters=VARS)
    assert errors == []


def test_nested_array_assignment() -> None:
    """Test nested array element assignment."""
    errors = check_method_body("arr[i][j] = 1;", parameters=VARS)
    assert errors == []


# =============================================================================
# More edge case coverage tests
# =============================================================================


def test_for_each_second_token_not_identifier() -> None:
    """Test for each where second token is not identifier."""
    # "for each 123 in list { }" - number instead of identifier
    errors = check_method_body("for each 123 in list { }", parameters=VARS)
    assert any(e.code == "MS-E041" for e in errors)


def test_empty_assignment_semicolon() -> None:
    """Test assignment with empty right side (semicolon immediately after =)."""
    # This should hit MS-E045 "Expected expression after '='"
    errors = check_method_body("y = x; x =;", parameters=VARS)
    # Should get either E045 or E048 for the empty assignment
    assert any(e.code in ("MS-E045", "MS-E048") for e in errors)


def test_multiply_incomplete() -> None:
    """Test incomplete multiplication expression."""
    errors = check_method_body("x = 2 *;", parameters=VARS)
    assert any(e.code == "MS-E046" for e in errors)


def test_divide_incomplete() -> None:
    """Test incomplete division expression."""
    errors = check_method_body("x = 2 /;", parameters=VARS)
    assert any(e.code == "MS-E046" for e in errors)


def test_user_property_syntax() -> None:
    """Test user property syntax with colon."""
    # obj._property:name syntax
    errors = check_method_body("x = obj._custom:PropertyName;", parameters=VARS)
    # This is valid syntax
    assert not any(e.code == "MS-E047" for e in errors)


def test_user_property_missing_name() -> None:
    """Test user property syntax with missing name after colon."""
    errors = check_method_body("x = obj._custom:;", parameters=VARS)
    assert any(e.code == "MS-E047" for e in errors)


def test_and_expression() -> None:
    """Test and expression."""
    errors = check_method_body("x = a and b;", parameters=VARS)
    assert errors == []


def test_or_expression() -> None:
    """Test or expression."""
    errors = check_method_body("x = a or b;", parameters=VARS)
    assert errors == []


def test_not_expression() -> None:
    """Test not expression."""
    errors = check_method_body("x = not a;", parameters=VARS)
    assert errors == []


def test_concat_incomplete() -> None:
    """Test incomplete concatenation expression."""
    errors = check_method_body("x = 'a' &;", parameters=VARS)
    assert any(e.code == "MS-E046" for e in errors)


def test_addition_incomplete() -> None:
    """Test incomplete addition expression."""
    errors = check_method_body("x = 1 +;", parameters=VARS)
    assert any(e.code == "MS-E046" for e in errors)


def test_subtraction_incomplete() -> None:
    """Test incomplete subtraction expression."""
    errors = check_method_body("x = 1 -;", parameters=VARS)
    # Minus can be unary, so this might parse as "1" then "-" then error
    assert len(errors) > 0


def test_comparison_incomplete() -> None:
    """Test incomplete comparison expression."""
    errors = check_method_body("x = a <;", parameters=VARS)
    # Gets unexpected token error
    assert any(e.code == "MS-E048" for e in errors)


def test_equality_incomplete() -> None:
    """Test incomplete equality expression."""
    errors = check_method_body("if (a =) { }", parameters=VARS)
    # Should error on empty after =
    assert len(errors) > 0


def test_switch_empty_body() -> None:
    """Test switch with empty body (no cases)."""
    errors = check_method_body("switch (x) { }", parameters=VARS)
    # Empty switch is actually valid (just does nothing)
    assert errors == []
