"""Tests for edge cases, error recovery, and branch coverage."""

from __future__ import annotations

from mahlif.sibelius.manuscript.checker import check_method_body
from mahlif.sibelius.manuscript.errors import LintError


def syntax_errors(errors: list[LintError]) -> list[LintError]:
    """Filter to only syntax errors, excluding semantic warnings."""
    excluded = {"MS-W025", "MS-W030", "MS-W033"}
    return [e for e in errors if e.code not in excluded]


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
# Error recovery
# =============================================================================


def test_error_token() -> None:
    """Test that ERROR tokens from tokenizer are handled."""
    errors = check_method_body("x = 'unterminated;")
    assert any(e.code == "MS-E030" for e in errors)


def test_expression_with_only_semicolon() -> None:
    """Test expression that starts with just semicolon - warns but no syntax error."""
    errors = check_method_body(";")
    assert syntax_errors(errors) == []
    assert any(e.code == "MS-W030" for e in errors)


def test_deeply_nested_recovery() -> None:
    """Test error recovery with nested blocks."""
    errors = check_method_body("if (x) { if (y) { z = 1; }", parameters=["x", "y", "z"])
    assert len(errors) > 0


def test_method_body_eof() -> None:
    """Test that method body ending at EOF is handled."""
    errors = check_method_body("x = 1")
    assert syntax_errors(errors) == []


def test_return_without_value() -> None:
    """Test return statement without a value."""
    errors = check_method_body("return;")
    assert syntax_errors(errors) == []


def test_return_before_rbrace() -> None:
    """Test return at end of block (no semicolon before brace)."""
    errors = check_method_body("if (x) { return }", parameters=["x"])
    assert any(e.code == "MS-E040" for e in errors)


def test_identifier_not_followed_by_assign() -> None:
    """Test identifier followed by something other than =."""
    errors = check_method_body("x + y;", parameters=["x", "y"])
    assert syntax_errors(errors) == []


def test_identifier_at_end() -> None:
    """Test identifier at end of tokens."""
    errors = check_method_body("x", parameters=["x"])
    assert syntax_errors(errors) == []


def test_recovery_to_eof() -> None:
    """Test error recovery that reaches EOF without finding brace."""
    errors = check_method_body("for i = 1 to 5 x = i;")
    assert len(errors) > 0


def test_unknown_character() -> None:
    """Test that unknown characters generate errors."""
    errors = check_method_body("x = `test`;", parameters=["x"])
    assert any(e.code == "MS-E031" for e in errors)


def test_string_with_newline() -> None:
    """Test unterminated string at newline."""
    errors = check_method_body("x = 'hello\nworld';", parameters=["x"])
    assert any(e.code == "MS-E030" for e in errors)


def test_multiline_code() -> None:
    """Test code with newlines exercises newline handling."""
    code = """x = 1;
y = 2;
z = x + y;"""
    errors = check_method_body(code, parameters=["x", "y", "z"])
    assert syntax_errors(errors) == []


def test_assignment_at_end_of_tokens() -> None:
    """Test assignment detection with minimal tokens (can't peek ahead)."""
    errors = check_method_body("x =")
    assert any(e.code.startswith("MS-E") for e in errors)


# =============================================================================
# Utility class tests
# =============================================================================


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


def test_unterminated_string_with_escape_at_end() -> None:
    """Test unterminated string ending with escape sequence."""
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    tokenizer = MethodBodyTokenizer("'a\\")
    tokens = list(tokenizer.tokenize())
    assert any(t.type.name == "ERROR" for t in tokens)
    assert any(e.code == "MS-E030" for e in tokenizer.errors)


# =============================================================================
# Branch coverage - internal methods
# =============================================================================


def test_arg_count_multiple_signatures() -> None:
    """Test error message with multiple overloaded signatures."""
    from mahlif.sibelius.manuscript.checker import (
        MethodBodyChecker,
        FunctionSignature,
        BUILTIN_SIGNATURES,
    )
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer
    from mahlif.sibelius.manuscript.tokens import Token, TokenType

    tokenizer = MethodBodyTokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)

    fake_token = Token(TokenType.IDENTIFIER, "TestFunc", 1, 1)

    BUILTIN_SIGNATURES["_TestMultiSig"] = [
        FunctionSignature(min_params=1, max_params=1),
        FunctionSignature(min_params=3, max_params=4),
    ]

    try:
        checker._check_arg_count(None, "_TestMultiSig", 2, fake_token)
        assert len(checker.errors) == 1
        assert "1 or 3-4" in checker.errors[0].message
    finally:
        del BUILTIN_SIGNATURES["_TestMultiSig"]


def test_arg_count_multiple_signatures_same_range() -> None:
    """Test error message with multiple signatures having same min=max."""
    from mahlif.sibelius.manuscript.checker import (
        MethodBodyChecker,
        FunctionSignature,
        BUILTIN_SIGNATURES,
    )
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer
    from mahlif.sibelius.manuscript.tokens import Token, TokenType

    tokenizer = MethodBodyTokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)

    fake_token = Token(TokenType.IDENTIFIER, "TestFunc", 1, 1)

    BUILTIN_SIGNATURES["_TestMultiSig2"] = [
        FunctionSignature(min_params=1, max_params=1),
        FunctionSignature(min_params=3, max_params=3),
    ]

    try:
        checker._check_arg_count(None, "_TestMultiSig2", 2, fake_token)
        assert len(checker.errors) == 1
        assert "1 or 3" in checker.errors[0].message
    finally:
        del BUILTIN_SIGNATURES["_TestMultiSig2"]


def test_find_similar_empty_candidates() -> None:
    """Test _find_similar with empty candidates list."""
    from mahlif.sibelius.manuscript.checker import MethodBodyChecker
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    tokenizer = MethodBodyTokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)

    result = checker._find_similar("test", set())
    assert result is None


def test_find_similar_empty_name() -> None:
    """Test _find_similar with empty name."""
    from mahlif.sibelius.manuscript.checker import MethodBodyChecker
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer

    tokenizer = MethodBodyTokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)

    result = checker._find_similar("", {"foo", "bar"})
    assert result is None or isinstance(result, str)


def test_arg_count_no_signature_data() -> None:
    """Test _check_arg_count returns early when no signature data."""
    from mahlif.sibelius.manuscript.checker import MethodBodyChecker
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer
    from mahlif.sibelius.manuscript.tokens import Token, TokenType

    tokenizer = MethodBodyTokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)

    fake_token = Token(TokenType.IDENTIFIER, "UnknownFunc", 1, 1)

    checker._check_arg_count(None, "UnknownFunctionWithNoSigData", 5, fake_token)
    assert not any(e.code == "MS-W023" for e in checker.errors)


def test_check_property_no_receiver_type() -> None:
    """Test _check_property returns early when receiver_type is None."""
    from mahlif.sibelius.manuscript.checker import MethodBodyChecker
    from mahlif.sibelius.manuscript.tokenizer import MethodBodyTokenizer
    from mahlif.sibelius.manuscript.tokens import Token, TokenType

    tokenizer = MethodBodyTokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    checker = MethodBodyChecker(tokens)

    fake_token = Token(TokenType.IDENTIFIER, "SomeProp", 1, 1)

    checker._check_property(None, "SomeProp", fake_token)
    assert not any(e.code == "MS-W024" for e in checker.errors)
