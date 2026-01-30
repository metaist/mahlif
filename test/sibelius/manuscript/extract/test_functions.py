"""Tests for get_builtin_functions and main entry point."""

from __future__ import annotations

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from mahlif.sibelius.manuscript.ast import Parser, Tokenizer, MethodDef
from mahlif.sibelius.manuscript.extract import get_builtin_functions
from mahlif.sibelius.manuscript.extract import main as extract_main


def test_get_builtin_functions() -> None:
    """Test getting built-in functions."""
    builtins = get_builtin_functions()
    assert "CreateSparseArray" in builtins
    assert builtins["CreateSparseArray"]["returns"] == "SparseArray"
    assert "Chr" in builtins
    assert builtins["Chr"]["params"] == ["code"]


def test_extract_main() -> None:
    """Test main reads from stdin and outputs JSON."""
    text = "\n" * 10001 + "Truth Values\nTrue\n\n1\n\nIndex\n"
    with patch.object(sys, "stdin") as mock_stdin:
        mock_stdin.read.return_value = text
        result = extract_main()
        assert result == 0


def test_extract_main_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with minimal input."""
    minimal_input = "\n" * 10001 + "Truth Values\nTrue\n\n1\n\nIndex\n"
    monkeypatch.setattr(sys, "stdin", StringIO(minimal_input))

    captured = StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    result = extract_main()
    assert result == 0

    output = json.loads(captured.getvalue())
    assert "objects" in output
    assert "constants" in output
    assert "builtin_functions" in output


def test_extract_main_with_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with objects that have methods."""
    test_input = (
        """
Barline
A Barline.

Methods
l

Test()
Test method.

Variables
l

Name
The name.
"""
        + "\n" * 10001
        + "Truth Values\nTrue\n\n1\n\nIndex\n"
    )

    monkeypatch.setattr(sys, "stdin", StringIO(test_input))

    captured = StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    result = extract_main()
    assert result == 0

    output = json.loads(captured.getvalue())
    assert "objects" in output
    assert "Barline" in output["objects"]
    barline = output["objects"]["Barline"]
    assert "methods" in barline
    assert "Test" in barline["methods"]
    assert "signatures" in barline["methods"]["Test"]


# =============================================================================
# AST helper tests (parameter extraction)
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
