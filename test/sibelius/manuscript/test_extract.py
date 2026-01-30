"""Tests for ManuScript language extraction module."""

from __future__ import annotations

import sys
from unittest.mock import patch


from mahlif.sibelius.manuscript.ast import Parser, Tokenizer, MethodDef
from mahlif.sibelius.manuscript.extract import extract_constants
from mahlif.sibelius.manuscript.extract import extract_objects
from mahlif.sibelius.manuscript.extract import get_builtin_functions
from mahlif.sibelius.manuscript.extract import main as extract_main
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


def test_extract_objects_basic() -> None:
    """Test extracting objects from PDF text."""
    # Simulate PDF structure
    text = """
Bar
A Bar contains BarObject objects.

Methods
l

AddNote(pos,pitch,dur)
Adds a note.

l

Delete()
Deletes.

Variables
l

Length
The length.

l

BarNumber
The bar number.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Bar" in objects
    bar = objects["Bar"]
    assert "AddNote" in bar.methods
    assert "Delete" in bar.methods
    assert "Length" in bar.properties
    assert "BarNumber" in bar.properties


def test_extract_objects_multiple() -> None:
    """Test extracting multiple object types."""
    text = """
Staff
A Staff.

Methods
l

NthBar(n)
Gets bar.

Variables
l

Name
The name.

Note
A Note.

Methods
l

Delete()
Deletes.

Variables
l

Pitch
The pitch.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Staff" in objects
    assert "Note" in objects
    assert "NthBar" in objects["Staff"].methods
    assert "Delete" in objects["Note"].methods


def test_extract_constants_basic() -> None:
    """Test extracting constants."""
    # Need to be after line 10000 and have "Truth Values"
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "True",
            "",
            "1",
            "",
            "False",
            "",
            "0",
            "",
            "Index",  # End marker
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("True") == 1
    assert constants.get("False") == 0


def test_extract_constants_with_aliases() -> None:
    """Test extracting constants with 'or' aliases."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "Quarter or Crotchet",
            "",
            "256",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("Quarter") == 256
    assert constants.get("Crotchet") == 256


def test_extract_constants_string_values() -> None:
    """Test extracting string constants."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "Alto",
            "",
            '"clef.alto"',
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("Alto") == "clef.alto"


def test_extract_constants_not_found() -> None:
    """Test when constants section not found."""
    lines = ["some text"] * 100
    constants = extract_constants(lines)
    assert constants == {}


def test_get_builtin_functions() -> None:
    """Test getting built-in functions."""
    builtins = get_builtin_functions()
    assert "CreateSparseArray" in builtins
    assert builtins["CreateSparseArray"]["returns"] == "SparseArray"
    assert "Chr" in builtins
    assert builtins["Chr"]["params"] == ["code"]


def test_extract_main() -> None:
    """Test main reads from stdin and outputs JSON."""
    # Minimal valid input
    text = "\n" * 10001 + "Truth Values\nTrue\n\n1\n\nIndex\n"
    with patch.object(sys, "stdin") as mock_stdin:
        mock_stdin.read.return_value = text
        result = extract_main()
        assert result == 0


# =============================================================================
# AST tests (moved from test_api.py)
# =============================================================================


def test_extract_params_empty_parens() -> None:
    """Test extracting params from empty parentheses."""
    tokens = list(Tokenizer('{ Test "() { }" }').tokenize())
    parser = Parser(tokens)
    plugin = parser.parse()
    if plugin.members:
        method = plugin.members[0]
        assert hasattr(method, "params")


def test_extract_params_empty_parens_whitespace() -> None:
    """Test extracting params from parens with only whitespace."""
    tokens = list(Tokenizer('{ Test "(   ) { }" }').tokenize())
    parser = Parser(tokens)
    plugin = parser.parse()
    assert len(plugin.members) == 1
    method = plugin.members[0]
    assert isinstance(method, MethodDef)
    assert method.params == []


def test_extract_params_no_parens() -> None:
    """Test extracting params from string without parentheses."""
    tokens = list(Tokenizer("{ }").tokenize())
    parser = Parser(tokens)
    result = parser._extract_params("no parens here")
    assert result == []
