"""Tests for ManuScript formatter API.

For comprehensive formatting tests, see test/sibelius/format/examples/.
"""

from __future__ import annotations

from pathlib import Path

from mahlif.sibelius.manuscript.format import format_file
from mahlif.sibelius.manuscript.format import format_file_in_place
from mahlif.sibelius.manuscript.format import format_plugin


def test_format_file(tmp_path: Path) -> None:
    """Test formatting a file."""
    plg = tmp_path / "test.plg"
    plg.write_text("""{
Initialize "() { AddToPluginsMenu('Test','Run'); }"
}""")

    result = format_file(plg)
    assert "Initialize" in result
    assert "AddToPluginsMenu" in result


def test_format_file_in_place(tmp_path: Path) -> None:
    """Test formatting file in place."""
    plg = tmp_path / "test.plg"
    original = """{
Initialize "() { x=1; }"
}"""
    plg.write_text(original)

    changed = format_file_in_place(plg)
    assert changed is True

    # Second time should return False (no change)
    changed = format_file_in_place(plg)
    assert changed is False


def test_format_file_with_bom(tmp_path: Path) -> None:
    """Test formatting file with BOM."""
    plg = tmp_path / "test.plg"
    plg.write_text("\ufeff{\n}", encoding="utf-8")

    result = format_file(plg)
    assert not result.startswith("\ufeff")


def test_format_plugin_empty() -> None:
    """Test formatting empty plugin."""
    result = format_plugin("{\n}")
    assert result == "{\n}\n"


def test_format_plugin_preserves_strings() -> None:
    """Test that non-method string content is preserved."""
    content = """{
    MyVar "some value with spaces"
}"""
    result = format_plugin(content)
    assert "some value with spaces" in result


def test_format_malformed_body_no_paren() -> None:
    """Test formatting body that doesn't start with (."""
    from mahlif.sibelius.manuscript.format import _format_method_body

    # Body without opening paren - returned as-is
    result = _format_method_body("no parens here")
    assert result == "no parens here"


def test_format_malformed_body_no_brace() -> None:
    """Test formatting body with params but no brace."""
    from mahlif.sibelius.manuscript.format import _format_method_body

    result = _format_method_body("(a, b) no brace")
    assert result == "(a, b) no brace"


def test_format_string_with_escape() -> None:
    """Test finding unescaped quote with escapes."""
    from mahlif.sibelius.manuscript.format import _find_unescaped_quote

    # String with escaped quote: hello\"world"
    result = _find_unescaped_quote('hello\\"world"')
    assert result == 12  # Position of final unescaped "


def test_format_consecutive_blank_lines() -> None:
    """Test that consecutive blank lines are collapsed."""
    content = """{


Initialize "() { }"


}"""
    result = format_plugin(content)
    # Should not have multiple consecutive blank lines
    assert "\n\n\n" not in result


def test_format_blank_line_at_start() -> None:
    """Test blank line at start of plugin."""
    content = """{

Initialize "() { }"
}"""
    result = format_plugin(content)
    assert "Initialize" in result


def test_format_unterminated_string() -> None:
    """Test plugin with unterminated string at end of file."""
    content = """{
Initialize "() { x = 1;
}"""
    # Should not crash, just pass through
    result = format_plugin(content)
    assert "{" in result


def test_format_unknown_line() -> None:
    """Test unknown line that's not a member definition."""
    content = """{
    some random text without quotes
    Initialize "() { }"
}"""
    result = format_plugin(content)
    # Unknown line should be preserved
    assert "some random text" in result


def test_format_unclosed_paren_in_body() -> None:
    """Test method body with unclosed parenthesis."""
    from mahlif.sibelius.manuscript.format import _format_method_body

    # Unclosed paren - should return as-is
    result = _format_method_body("(a, b")
    assert result == "(a, b"


def test_format_unclosed_brace_in_body() -> None:
    """Test method body with unclosed brace."""
    from mahlif.sibelius.manuscript.format import _format_method_body

    # Params ok but unclosed brace
    result = _format_method_body("(a, b) { x = 1;")
    assert result == "(a, b) { x = 1;"


def test_format_empty_make_line() -> None:
    """Test _make_line with empty content."""
    from mahlif.sibelius.manuscript.format import _make_line

    result = _make_line([], 0)
    assert result == ""

    result = _make_line(["   "], 0)  # Only whitespace
    assert result == ""


def test_format_strips_trailing_space_before_paren() -> None:
    """Test that trailing space is stripped before )."""
    from mahlif.sibelius.manuscript.format import _format_statements

    # "foo( a )" should become "foo(a)"
    result = _format_statements("foo( a );")
    assert "foo(a)" in result


def test_format_operator_before_paren() -> None:
    """Test trailing space stripped when operator precedes )."""
    from mahlif.sibelius.manuscript.format import _format_statements

    # Malformed but tests _strip_trailing_space path
    # Operator adds " + ", then ) should strip the trailing space
    result = _format_statements("x = (a +);")
    # Should have "+" right before ")"
    assert "+)" in result


def test_format_nested_parens_in_params() -> None:
    """Test method with nested parentheses in parameters."""
    from mahlif.sibelius.manuscript.format import _format_method_body

    # Nested parens in param list
    result = _format_method_body("(a, (b, c)) { x = 1; }")
    assert "a, (b, c)" in result or "(b, c)" in result
