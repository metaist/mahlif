"""Tests for extract_constants function and section header detection."""

from __future__ import annotations

from mahlif.sibelius.manuscript.extract import extract_constants
from mahlif.sibelius.manuscript.extract import _is_section_header
from mahlif.sibelius.manuscript.extract import RegexMatch


def test_extract_constants_basic() -> None:
    """Test extracting constants."""
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
            "Index",
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
    assert "This" not in constants


def test_extract_constants_skips_section_headers() -> None:
    """Test that section headers inside constants section are skipped."""
    lines = [""] * 10001
    lines.extend(
        [
            "7 Global Constants",
            "Truth Values",
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
            "NoValue",
            "True",
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert "NoValue" not in constants
    assert constants.get("True") == 1


def test_extract_constants_string_with_or() -> None:
    """Test extracting string constants with 'or' aliases."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
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


def test_extract_constants_value_search_exhausted() -> None:
    """Test when value search loop exhausts without finding value."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "SomeConstant",
            "",
            "",
            "",
            "",
            "",
            "NextConstant",
            "",
            "1",
            "",
            "Index",
        ]
    )
    constants = extract_constants(lines)
    assert "SomeConstant" not in constants
    assert constants.get("NextConstant") == 1


def test_extract_constants_non_matching_line() -> None:
    """Test that non-matching lines are skipped."""
    lines = [""] * 10001
    lines.extend(
        [
            "Truth Values",
            "lowercase_not_a_constant",
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
        ]
    )
    constants = extract_constants(lines)
    assert constants.get("True") == 1


def test_extract_constants_multiline() -> None:
    """Test extraction of constants spanning multiple lines before value."""
    lines = [""] * 10001
    lines.append("Truth Values")
    lines.append("TestConstant")
    lines.append("")
    lines.append("42")
    lines.append("")
    lines.append("AnotherConstant")
    lines.append("99")
    lines.append("Index")

    constants = extract_constants(lines)

    assert "TestConstant" in constants
    assert constants["TestConstant"] == 42
    assert "AnotherConstant" in constants
    assert constants["AnotherConstant"] == 99


def test_extract_constants_unknown_pattern() -> None:
    """Test constant extraction handles unknown patterns."""
    lines = [""] * 10001
    lines.append("Truth Values")
    lines.append("TestConstant")
    lines.append("some random text that matches nothing")
    lines.append("42")
    lines.append("Index")

    constants = extract_constants(lines)
    assert "TestConstant" in constants
    assert constants["TestConstant"] == 42


# =============================================================================
# Section header heuristic tests
# =============================================================================


def test_is_section_header_with_spaces_and_roman() -> None:
    """Test section header detection with spaces and Roman numeral."""
    # cspell:ignore clxxxi clxxxii
    assert _is_section_header("Truth Values", ["", "clxxxi", ""])
    assert _is_section_header("Bar Number Formats", ["clxxxii"])


def test_is_section_header_values_pattern() -> None:
    """Test section header detection with 'Values' pattern."""
    assert _is_section_header("InMultirest Values", [])
    assert _is_section_header("Units Values", [])


def test_is_section_header_types_pattern() -> None:
    """Test section header detection with 'Types' pattern."""
    assert _is_section_header("Instrument Types", [])
    assert _is_section_header("Bracket Types", [])


def test_is_section_header_chapter() -> None:
    """Test chapter header detection."""
    assert _is_section_header("7 Global Constants", [])


def test_is_section_header_chapter_7() -> None:
    """Test that '7 Global Constants' is recognized as chapter header."""
    assert _is_section_header("7 Global Constants", [])


def test_is_section_header_no_match() -> None:
    """Test that 'Contents' alone (no spaces, no pattern) is not a header."""
    assert not _is_section_header("Contents", [])


def test_is_section_header_not_constant() -> None:
    """Test that single PascalCase words are not headers."""
    assert not _is_section_header("True", [])
    assert not _is_section_header("Quarter", [])
    assert not _is_section_header("MiddleOfWord", [])


def test_is_section_header_empty() -> None:
    """Test empty/short lines are not headers."""
    assert not _is_section_header("", [])
    assert not _is_section_header("ab", [])


def test_is_section_header_long_description() -> None:
    """Test long lines (descriptions) are not headers."""
    long_text = "This is a long description that explains something about the API"
    assert not _is_section_header(long_text, [])


def test_is_section_header_long_with_spaces() -> None:
    """Test that long lines with spaces are not headers."""
    long_line = (
        "This is a very long line with spaces that exceeds sixty characters total"
    )
    assert not _is_section_header(long_line, [])


# =============================================================================
# RegexMatch utility tests
# =============================================================================


def test_regex_match_non_string_comparison() -> None:
    """Test RegexMatch falls back to str.__eq__ for non-string comparison."""
    rm = RegexMatch("hello")
    assert (rm == 123) is False
    assert hash(rm) == hash("hello")
