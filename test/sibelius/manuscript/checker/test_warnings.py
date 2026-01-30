"""Tests for semantic warnings (MS-W0XX)."""

from __future__ import annotations

from mahlif.sibelius.manuscript.checker import check_method_body
from mahlif.sibelius.manuscript.errors import LintError


def syntax_errors(errors: list[LintError]) -> list[LintError]:
    """Filter to only syntax errors, excluding semantic warnings."""
    excluded = {"MS-W025", "MS-W030", "MS-W033"}
    return [e for e in errors if e.code not in excluded]


# =============================================================================
# MS-W020: Undefined variable detection
# =============================================================================


def test_undefined_variable_warning() -> None:
    """Test undefined variable generates warning."""
    errors = check_method_body("x = undefined_var;")
    assert any(e.code == "MS-W020" for e in errors)


def test_variable_defined_by_assignment() -> None:
    """Test variable is defined after assignment."""
    errors = check_method_body("x = 1; y = x;")
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
    errors = check_method_body("x.NthBar(1);", parameters=["x"])
    assert syntax_errors(errors) == []


def test_chained_property_then_method() -> None:
    """Test chained access doesn't false-positive."""
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
    )
    w022_errors = [e for e in errors if e.code == "MS-W022"]
    assert len(w022_errors) == 1


def test_object_name_as_function() -> None:
    """Test that using object type name as function doesn't warn."""
    errors = check_method_body("x = Sibelius();")
    w022_errors = [e for e in errors if e.code == "MS-W022"]
    assert w022_errors == []


def test_call_method_on_any_object() -> None:
    """Test that methods existing on ANY object don't warn when receiver unknown."""
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
    errors = check_method_body("x = Substring('hello', 0, 5);")
    w023_errors = [e for e in errors if e.code == "MS-W023"]
    assert w023_errors == []


def test_arg_count_range_signature() -> None:
    """Test wrong arg count error for function with min != max signature."""
    errors = check_method_body("x = Substring();")
    w023_errors = [e for e in errors if e.code == "MS-W023"]
    assert len(w023_errors) == 1
    assert "2-3" in w023_errors[0].message


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


def test_check_property_method_access() -> None:
    """Test property check when accessing a method name without calling it."""
    errors = check_method_body("x = Sibelius.ActiveScore;")
    errors = check_method_body("x = Sibelius.MessageBox;")
    assert not any("MessageBox" in e.message and e.code == "MS-W024" for e in errors)


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
    assert not any("'x'" in e.message for e in w025_errors)
    assert any("'y'" in e.message for e in w025_errors)


def test_parameter_not_unused() -> None:
    """Test parameters are not flagged as unused."""
    errors = check_method_body("y = 1;", parameters=["x"])
    w025_errors = [e for e in errors if e.code == "MS-W025"]
    assert not any("'x'" in e.message for e in w025_errors)
    assert any("'y'" in e.message for e in w025_errors)


def test_loop_variable_not_unused() -> None:
    """Test loop variables are not flagged as unused."""
    errors = check_method_body("for i = 0 to 10 { }")
    w025_errors = [e for e in errors if e.code == "MS-W025"]
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


def test_unreachable_code_warns_only_once() -> None:
    """Test that unreachable code after return only warns once."""
    errors = check_method_body("return 1; x = 1; y = 2;")
    w026_errors = [e for e in errors if e.code == "MS-W026"]
    assert len(w026_errors) == 1


def test_unreachable_code_second_statement_skips_warning() -> None:
    """Test that second unreachable statement doesn't trigger re-check."""
    from mahlif.sibelius.manuscript.checker import MethodBodyChecker
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    code = "return 1; x = 1; y = 2; z = 3;"
    tokenizer = MethodBodyTokenizer(code)
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)
    errors = checker.check()

    w026_errors = [e for e in errors if e.code == "MS-W026"]
    assert len(w026_errors) == 1
    assert checker.unreachable_warned is True


def test_return_in_block_followed_by_brace() -> None:
    """Test return in if block where next token is closing brace."""
    errors = check_method_body("if (x) { return 1; }", parameters=["x"])
    w026_errors = [e for e in errors if e.code == "MS-W026"]
    assert w026_errors == []


def test_return_at_end_of_block_no_unreachable() -> None:
    """Test return at end of block doesn't warn about unreachable code."""
    errors = check_method_body("x = 1; return x;")
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


def test_constant_condition_nonzero_number() -> None:
    """Test warning for if (42) - nonzero number."""
    errors = check_method_body("if (1) { x = 1; }")
    w028_errors = [e for e in errors if e.code == "MS-W028"]
    assert len(w028_errors) == 1
    assert "always true" in w028_errors[0].message


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


def test_comparison_to_self_lt() -> None:
    """Test warning for x < x (always false)."""
    errors = check_method_body("if (x < x) { }", parameters=["x"])
    assert any(e.code == "MS-W032" and "always false" in e.message for e in errors)


def test_comparison_to_self_gt() -> None:
    """Test warning for x > x (always false)."""
    errors = check_method_body("if (x > x) { }", parameters=["x"])
    assert any(e.code == "MS-W032" and "always false" in e.message for e in errors)


def test_comparison_to_self_lte() -> None:
    """Test warning for x <= x (always true)."""
    errors = check_method_body("if (x <= x) { }", parameters=["x"])
    assert any(e.code == "MS-W032" and "always true" in e.message for e in errors)


def test_comparison_to_self_gte() -> None:
    """Test warning for x >= x (always true)."""
    errors = check_method_body("if (x >= x) { }", parameters=["x"])
    assert any(e.code == "MS-W032" and "always true" in e.message for e in errors)


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
