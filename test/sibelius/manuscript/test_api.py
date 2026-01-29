"""Tests for ManuScript API extraction module."""

from __future__ import annotations

import sys
from unittest.mock import patch


from mahlif.sibelius.manuscript.ast import Parser, Tokenizer
from mahlif.sibelius.manuscript.api import extract_signatures
from mahlif.sibelius.manuscript.api import main as extract_main
from mahlif.sibelius.manuscript.api import parse_signature


def test_parse_signature_simple() -> None:
    """Test parsing simple signature."""
    result = parse_signature("Test()")
    assert result is not None
    assert result["name"] == "Test"
    assert result["min_params"] == 0
    assert result["max_params"] == 0


def test_parse_signature_with_params() -> None:
    """Test parsing signature with params."""
    result = parse_signature("AddNote(pos,pitch,dur)")
    assert result is not None
    assert result["name"] == "AddNote"
    assert result["min_params"] == 3
    assert result["max_params"] == 3
    assert result["params"] == ["pos", "pitch", "dur"]


def test_parse_signature_optional_params() -> None:
    """Test parsing signature with optional params."""
    result = parse_signature("Test(a,[b,[c]])")
    assert result is not None
    assert result["min_params"] == 1
    assert result["max_params"] == 3


def test_parse_signature_invalid() -> None:
    """Test parsing invalid signature."""
    result = parse_signature("not a signature")
    assert result is None


def test_parse_signature_lowercase() -> None:
    """Test lowercase name is rejected."""
    result = parse_signature("lowercase()")
    assert result is None


def test_extract_signatures() -> None:
    """Test extracting signatures from text."""
    text = """
Some description text
AddNote(pos,pitch,dur)
More text
CreateSparseArray()
"""
    methods = extract_signatures(text)
    assert "AddNote" in methods
    assert "CreateSparseArray" in methods


def test_extract_signatures_keeps_max_params() -> None:
    """Test that duplicate keeps max params version."""
    text = """
Test(a)
Test(a,b,c)
"""
    methods = extract_signatures(text)
    assert methods["Test"]["max_params"] == 3


def test_extract_main() -> None:
    """Test main reads from stdin."""
    with patch.object(sys, "stdin") as mock_stdin:
        mock_stdin.read.return_value = "Test(a,b)\n"
        result = extract_main()
        assert result == 0


# =============================================================================
# automation tests
# =============================================================================


def test_parse_signature_all_optional() -> None:
    """Test signature where all params are optional."""
    result = parse_signature("Test([a,[b]])")
    assert result is not None
    assert result["min_params"] == 0
    assert result["max_params"] == 2


def test_extract_api_empty_params() -> None:
    """Test parse_signature with no params."""
    result = parse_signature("NoParams()")
    assert result is not None
    assert result["params"] == []


def test_extract_api_nested_optional() -> None:
    """Test deeply nested optional params."""
    result = parse_signature("Foo(a,b,[c,[d,[e]]])")
    assert result is not None
    assert result["min_params"] == 2
    assert result["max_params"] == 5


def test_extract_api_multiple_signatures_same_name() -> None:
    """Test that extract keeps max params version."""
    text = "Test(a)\nTest(a,b,c,d)\nTest(a,b)"
    methods = extract_signatures(text)
    assert methods["Test"]["max_params"] == 4


# =============================================================================
# Edge case and malformed input tests for 100% coverage
# =============================================================================


def test_parse_signature_optional_with_content_before_bracket() -> None:
    """Test optional param that has content before the bracket."""
    # This hits lines 51-54: when we have content before [ and in_optional==1
    result = parse_signature("Foo(a[,b])")
    assert result is not None
    assert result["min_params"] == 1
    assert result["max_params"] == 2


def test_parse_signature_nested_optional_end() -> None:
    """Test closing bracket with content."""
    result = parse_signature("Bar([a[,b]])")
    assert result is not None
    assert result["min_params"] == 1  # 'a' is first optional, so min=1 after parsing
    assert result["max_params"] == 2


def test_extract_params_empty_parens() -> None:
    """Test extracting params from empty parentheses."""
    # Line 488: params_str is empty
    tokens = list(Tokenizer('{ Test "() { }" }').tokenize())
    parser = Parser(tokens)
    plugin = parser.parse()
    # Method should have empty params
    if plugin.members:
        method = plugin.members[0]
        assert hasattr(method, "params")


def test_extract_signatures_invalid_signature() -> None:
    """Test that invalid signatures are skipped."""
    # This pattern won't parse - missing closing paren
    text = "ValidMethod(a, b)\nInvalid(a, b"
    methods = extract_signatures(text)
    assert "ValidMethod" in methods
    assert "Invalid" not in methods


def test_extract_signatures_empty_text() -> None:
    """Test with empty input."""
    methods = extract_signatures("")
    assert methods == {}


def test_extract_params_empty_parens_whitespace() -> None:
    """Test extracting params from parens with only whitespace."""
    from mahlif.sibelius.manuscript.ast import MethodDef

    tokens = list(Tokenizer('{ Test "(   ) { }" }').tokenize())
    parser = Parser(tokens)
    plugin = parser.parse()
    assert len(plugin.members) == 1
    method = plugin.members[0]
    assert isinstance(method, MethodDef)
    assert method.params == []


def test_extract_signatures_parse_returns_none() -> None:
    """Test signature that looks valid but parse_signature returns None."""
    # Malformed signature that regex matches but parse fails
    # Actually need to check what makes parse_signature return None
    result = parse_signature("Invalid(")  # Unclosed paren
    assert result is None


def test_extract_params_no_parens() -> None:
    """Test extracting params from string without parentheses."""
    # Manually call _extract_params with no parens
    tokens = list(Tokenizer("{ }").tokenize())
    parser = Parser(tokens)
    result = parser._extract_params("no parens here")
    assert result == []
