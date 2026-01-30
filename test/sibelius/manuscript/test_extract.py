"""Tests for ManuScript language extraction module."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

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


# =============================================================================
# Section header heuristic tests
# =============================================================================


def test_is_section_header_with_spaces_and_roman() -> None:
    """Test section header detection with spaces and Roman numeral."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    # cspell:ignore clxxxi clxxxii
    assert _is_section_header("Truth Values", ["", "clxxxi", ""])
    assert _is_section_header("Bar Number Formats", ["clxxxii"])


def test_is_section_header_values_pattern() -> None:
    """Test section header detection with 'Values' pattern."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    assert _is_section_header("InMultirest Values", [])
    assert _is_section_header("Units Values", [])


def test_is_section_header_types_pattern() -> None:
    """Test section header detection with 'Types' pattern."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    assert _is_section_header("Instrument Types", [])
    assert _is_section_header("Bracket Types", [])


def test_is_section_header_chapter() -> None:
    """Test chapter header detection."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    assert _is_section_header("7 Global Constants", [])


def test_is_section_header_no_match() -> None:
    """Test that 'Contents' alone (no spaces, no pattern) is not a header."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    # Single word without matching pattern is not a header
    assert not _is_section_header("Contents", [])


def test_is_section_header_not_constant() -> None:
    """Test that single PascalCase words are not headers."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    assert not _is_section_header("True", [])
    assert not _is_section_header("Quarter", [])
    assert not _is_section_header("MiddleOfWord", [])


def test_is_section_header_empty() -> None:
    """Test empty/short lines are not headers."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    assert not _is_section_header("", [])
    assert not _is_section_header("ab", [])


def test_is_section_header_long_description() -> None:
    """Test long lines (descriptions) are not headers."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    long_text = "This is a long description that explains something about the API"
    assert not _is_section_header(long_text, [])


# =============================================================================
# Main function test
# =============================================================================


def test_extract_main_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with minimal input."""
    import sys
    from io import StringIO
    from mahlif.sibelius.manuscript.extract import main

    # Minimal input that produces valid JSON
    minimal_input = "\n" * 10001 + "Truth Values\nTrue\n\n1\n\nIndex\n"
    monkeypatch.setattr(sys, "stdin", StringIO(minimal_input))

    # Capture stdout
    captured = StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    result = main()
    assert result == 0

    # Check output is valid JSON
    import json

    output = json.loads(captured.getvalue())
    assert "objects" in output
    assert "constants" in output
    assert "builtin_functions" in output


# =============================================================================
# Additional coverage tests
# =============================================================================


def test_extract_objects_duplicate_object() -> None:
    """Test extracting an object defined in multiple places merges methods."""
    # Same object name appears twice - second occurrence adds more methods
    # The merge logic in lines 249-253 extends methods and properties
    text = """
Barline
A Barline object.

Methods
l

Test1()
First method.

Variables
l

Aa
Property one.

Barline
More Barline docs.

Methods
l

Test2()
Second method.

Variables
l

Bb
Property two.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Barline" in objects
    barline = objects["Barline"]
    # Should have methods from both definitions (merged)
    assert "Test1" in barline.methods
    assert "Test2" in barline.methods
    # Properties get extended from both definitions
    assert "Aa" in barline.properties
    assert "Bb" in barline.properties


def test_extract_constants_skips_long_descriptions() -> None:
    """Test that long description lines are skipped."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "This is a very long description line that should be skipped entirely",
            "True",
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("True") == 1
    # The long line should not be treated as a constant name
    assert "This" not in constants


def test_extract_constants_skips_section_headers() -> None:
    """Test that section headers inside constants section are skipped."""
    lines = [""] * 10001
    lines.extend(
        [
            "7 Global Constants",  # Chapter header
            "Truth Values",  # Section header with known pattern
            "True",
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("True") == 1


def test_extract_constants_hits_next_constant() -> None:
    """Test when searching for value hits the next constant name."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "NoValue",  # Constant without a value line
            "True",  # This is the next constant, should stop search
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    # NoValue should not be in constants since we hit True before finding value
    assert "NoValue" not in constants
    assert constants.get("True") == 1


def test_parse_signature_closing_bracket_with_content() -> None:
    """Test closing bracket with content in current param."""
    # This tests line 128-130: ] with current_param having content
    result = parse_signature("Foo(a,[b])")
    assert result is not None
    _, sig = result
    assert sig.params == ["a", "b?"]
    assert sig.min_params == 1
    assert sig.max_params == 2


def test_extract_objects_skip_object_reference_header() -> None:
    """Test that '4 Object Reference' line is skipped."""
    text = """
4 Object Reference

Bar
A Bar.

Methods
l

Test()
Test method.

Variables
l

Name
The name.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Bar" in objects
    # "4 Object Reference" should not be an object
    assert "4" not in objects
    assert "4 Object Reference" not in objects


def test_extract_main_with_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with objects that have methods."""
    import sys
    import json
    from io import StringIO
    from mahlif.sibelius.manuscript.extract import main

    # Input with an object that has a method
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

    result = main()
    assert result == 0

    output = json.loads(captured.getvalue())
    assert "objects" in output
    assert "Barline" in output["objects"]
    barline = output["objects"]["Barline"]
    assert "methods" in barline
    assert "Test" in barline["methods"]
    assert "signatures" in barline["methods"]["Test"]


def test_is_section_header_long_with_spaces() -> None:
    """Test that long lines with spaces are not headers."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    # > 60 chars with spaces should return False early
    long_line = (
        "This is a very long line with spaces that exceeds sixty characters total"
    )
    assert not _is_section_header(long_line, [])


def test_extract_constants_string_with_or() -> None:
    """Test extracting string constants with 'or' aliases."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",  # Must start with this marker
            "Alto or Tenor",
            "",
            '"clef.alto"',
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("Alto") == "clef.alto"
    assert constants.get("Tenor") == "clef.alto"


def test_extract_objects_with_4_object_reference() -> None:
    """Test that '4 Object Reference' line inside object is skipped."""
    text = """
Barline
A Barline.

Methods
l

4 Object Reference

Test()
Test method.

Variables
l

Name
The name.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Barline" in objects
    # "4 Object Reference" should not be parsed as a method
    assert "4" not in objects["Barline"].methods
    assert "Test" in objects["Barline"].methods


def test_extract_constants_value_search_exhausted() -> None:
    """Test when value search loop exhausts without finding value."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "SomeConstant",
            # 5 blank lines - search will exhaust
            "",
            "",
            "",
            "",
            "",
            "NextConstant",  # This is line 6, beyond search range
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    # SomeConstant should not be found (value search exhausted)
    assert "SomeConstant" not in constants
    # NextConstant should be found
    assert constants.get("NextConstant") == 1


def test_extract_constants_non_matching_line() -> None:
    """Test that non-matching lines are skipped."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "lowercase_not_a_constant",  # doesn't match [A-Z] pattern
            "True",
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("True") == 1
    assert "lowercase_not_a_constant" not in constants


def test_parse_signature_empty_optional_bracket() -> None:
    """Test parsing signature with empty optional brackets."""
    # This exercises the branch where ] follows [ directly
    result = parse_signature("Foo(a,[])")
    assert result is not None
    _, sig = result
    # Empty brackets don't add params
    assert sig.params == ["a"]
    assert sig.min_params == 1
    assert sig.max_params == 1


def test_extract_objects_method_overload() -> None:
    """Test extracting overloaded methods (same name, different signatures)."""
    text = """
Barline
A Barline.

Methods
l

Test(a)
One param.

l

Test(a,b)
Two params.

Variables
l

Name
The name.
"""
    objects = extract_objects(list(text.split("\n")))
    assert "Barline" in objects
    barline = objects["Barline"]
    assert "Test" in barline.methods
    # Should have both signatures
    sigs = barline.methods["Test"]
    assert len(sigs) == 2


def test_is_section_header_chapter_7() -> None:
    """Test that '7 Global Constants' is recognized as chapter header."""
    from mahlif.sibelius.manuscript.extract import _is_section_header

    assert _is_section_header("7 Global Constants", [])


def test_extract_constants_no_index_marker() -> None:
    """Test constants extraction when Index marker is missing."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "True",
            "",
            "1",
            "",
            # No Index marker - should read to end
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("True") == 1


def test_parse_signature_optional_mid_params() -> None:
    """Test parse_signature with optional marker mid-params."""
    from mahlif.sibelius.manuscript.extract import parse_signature

    # Format: (required, [optional1, optional2])
    result = parse_signature("TestMethod(a, [b, c])")
    assert result is not None
    name, sig = result
    assert name == "TestMethod"
    assert sig.min_params == 1  # Only 'a' is required
    assert sig.max_params == 3  # a, b, c


def test_extract_duplicate_method_name() -> None:
    """Test extraction handles duplicate method names (merges signatures)."""
    from mahlif.sibelius.manuscript.extract import extract_objects

    # Simulate PDF text with duplicate method in same object
    # Need proper PascalCase object name followed by Methods within 15 lines
    lines = [
        "Sibelius",
        "Description of Sibelius object",
        "Methods",
        "TestMethod()",
        "TestMethod(param1)",
        "Variables",
        "SomeProp",
        "",
        "Bar",
        "Description of Bar",
        "Methods",
        "OtherMethod()",
    ]
    objects = extract_objects(lines)

    # Should have merged both signatures
    assert "Sibelius" in objects
    assert "TestMethod" in objects["Sibelius"].methods
    assert len(objects["Sibelius"].methods["TestMethod"]) == 2


def test_extract_object_split_across_pages() -> None:
    """Test extraction handles object split across pages (same name twice)."""
    from mahlif.sibelius.manuscript.extract import extract_objects

    # Sibelius object appears twice - simulating page break in PDF
    lines = [
        "Sibelius",
        "First description",
        "Methods",
        "FirstMethod()",
        "",
        "Bar",
        "Bar description",
        "Methods",
        "BarMethod()",
        "",
        "Sibelius",  # Same object again (page 2)
        "Continued description",
        "Methods",
        "FirstMethod(x)",  # Same method, different signature
        "SecondMethod()",
        "Variables",
        "ExtraProp",
    ]
    objects = extract_objects(lines)

    assert "Sibelius" in objects
    # FirstMethod should have 2 signatures merged
    assert "FirstMethod" in objects["Sibelius"].methods
    assert len(objects["Sibelius"].methods["FirstMethod"]) == 2
    # SecondMethod should also be present
    assert "SecondMethod" in objects["Sibelius"].methods


def test_extract_constants_multiline() -> None:
    """Test extraction of constants spanning multiple lines before value."""
    from mahlif.sibelius.manuscript.extract import extract_constants

    # Need "Truth Values" after line 10000
    # Create enough lines to get past the threshold
    lines = [""] * 10001
    lines.append("Truth Values")
    lines.append("TestConstant")
    lines.append("")  # blank line - should loop back
    lines.append("42")
    lines.append("")
    lines.append("AnotherConstant")
    lines.append("99")
    lines.append("Index")  # End marker

    constants = extract_constants(lines)

    assert "TestConstant" in constants
    assert constants["TestConstant"] == 42
    assert "AnotherConstant" in constants
    assert constants["AnotherConstant"] == 99


def test_regex_match_non_string_comparison() -> None:
    """Test RegexMatch falls back to str.__eq__ for non-string comparison."""
    from mahlif.sibelius.manuscript.extract import RegexMatch

    rm = RegexMatch("hello")
    # Compare with non-string (int)
    assert (rm == 123) is False
    # Test hash works
    assert hash(rm) == hash("hello")


def test_extract_constants_unknown_pattern() -> None:
    """Test constant extraction handles unknown patterns (not int, string, or name)."""
    from mahlif.sibelius.manuscript.extract import extract_constants

    # Need "Truth Values" after line 10000
    lines = [""] * 10001
    lines.append("Truth Values")
    lines.append("TestConstant")
    lines.append("some random text that matches nothing")  # Unknown pattern
    lines.append("42")  # Should still find this
    lines.append("Index")

    constants = extract_constants(lines)
    assert "TestConstant" in constants
    assert constants["TestConstant"] == 42


def test_parse_signature_nested_bracket_with_param() -> None:
    """Test nested bracket where param exists before inner bracket."""
    from mahlif.sibelius.manuscript.extract import parse_signature

    # (a,[bc[d]]) - 'bc' is before nested [, in_optional becomes 2
    # When second [ is hit, bc gets appended but min_params not set (in_optional==2)
    result = parse_signature("Test(a,[bc[d]])")
    assert result is not None
    name, sig = result
    assert name == "Test"
    # 'a' and 'bc' counted before nested optional, 'd' is deeply optional
    assert sig.min_params == 2  # bc was appended before in_optional check
    assert sig.max_params == 3
