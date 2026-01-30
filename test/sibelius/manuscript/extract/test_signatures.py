"""Tests for parse_signature function."""

from __future__ import annotations

from mahlif.sibelius.manuscript.extract import parse_signature


def test_parse_signature_simple() -> None:
    """Test parsing simple signature."""
    result = parse_signature("Test()")
    assert result is not None
    name, sig = result
    assert name == "Test"
    assert sig.min_params == 0
    assert sig.max_params == 0


def test_parse_signature_with_params() -> None:
    """Test parsing signature with params."""
    result = parse_signature("AddNote(pos,pitch,dur)")
    assert result is not None
    name, sig = result
    assert name == "AddNote"
    assert sig.min_params == 3
    assert sig.max_params == 3
    assert sig.params == ["pos", "pitch", "dur"]


def test_parse_signature_optional_params() -> None:
    """Test parsing signature with optional params."""
    result = parse_signature("Test(a,[b,[c]])")
    assert result is not None
    _, sig = result
    assert sig.min_params == 1
    assert sig.max_params == 3


def test_parse_signature_invalid() -> None:
    """Test parsing invalid signature."""
    result = parse_signature("not a signature")
    assert result is None


def test_parse_signature_lowercase() -> None:
    """Test lowercase name is rejected."""
    result = parse_signature("lowercase()")
    assert result is None


def test_parse_signature_all_optional() -> None:
    """Test signature where all params are optional."""
    result = parse_signature("Test([a,[b]])")
    assert result is not None
    _, sig = result
    assert sig.min_params == 0
    assert sig.max_params == 2


def test_parse_signature_nested_optional() -> None:
    """Test deeply nested optional params."""
    result = parse_signature("Foo(a,b,[c,[d,[e]]])")
    assert result is not None
    _, sig = result
    assert sig.min_params == 2
    assert sig.max_params == 5


def test_parse_signature_optional_with_content_before_bracket() -> None:
    """Test optional param that has content before the bracket."""
    result = parse_signature("Foo(a[,b])")
    assert result is not None
    _, sig = result
    assert sig.min_params == 1
    assert sig.max_params == 2


def test_parse_signature_unclosed() -> None:
    """Test signature with unclosed paren."""
    result = parse_signature("Invalid(")
    assert result is None


def test_parse_signature_closing_bracket_with_content() -> None:
    """Test closing bracket with content in current param."""
    result = parse_signature("Foo(a,[b])")
    assert result is not None
    _, sig = result
    assert sig.params == ["a", "b?"]
    assert sig.min_params == 1
    assert sig.max_params == 2


def test_parse_signature_empty_optional_bracket() -> None:
    """Test parsing signature with empty optional brackets."""
    result = parse_signature("Foo(a,[])")
    assert result is not None
    _, sig = result
    assert sig.params == ["a"]
    assert sig.min_params == 1
    assert sig.max_params == 1


def test_parse_signature_optional_mid_params() -> None:
    """Test parse_signature with optional marker mid-params."""
    result = parse_signature("TestMethod(a, [b, c])")
    assert result is not None
    name, sig = result
    assert name == "TestMethod"
    assert sig.min_params == 1
    assert sig.max_params == 3


def test_parse_signature_nested_bracket_with_param() -> None:
    """Test nested bracket where param exists before inner bracket."""
    result = parse_signature("Test(a,[bc[d]])")
    assert result is not None
    name, sig = result
    assert name == "Test"
    assert sig.min_params == 2
    assert sig.max_params == 3
