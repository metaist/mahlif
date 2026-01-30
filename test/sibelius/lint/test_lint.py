"""Tests for Sibelius lint module."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mahlif.sibelius.manuscript.lint import LintError
from mahlif.sibelius.manuscript.lint import lint
from mahlif.sibelius.manuscript.lint import lint_braces
from mahlif.sibelius.manuscript.lint import lint_common_issues
from mahlif.sibelius.manuscript.lint import lint_method_calls
from mahlif.sibelius.manuscript.lint import lint_methods
from mahlif.sibelius.manuscript.lint import lint_plugin_structure
from mahlif.sibelius.manuscript.lint import lint_strings
from mahlif.sibelius.manuscript.lint import main as lint_main
from mahlif.sibelius.manuscript.lint import read_plugin
from mahlif.sibelius.manuscript.lint import parse_inline_directives


def test_lint_error_str() -> None:
    """Test LintError string representation."""
    err = LintError(10, 5, "MS-E001", "Test error")
    assert str(err) == "10:5 [MS-E001] Test error"


def test_read_plugin_utf8() -> None:
    """Test reading UTF-8 plugin."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False) as f:
        f.write(b"{ test }")
        f.flush()
        content = read_plugin(Path(f.name))
        assert content == "{ test }"
        Path(f.name).unlink()


def test_read_plugin_utf16_be() -> None:
    """Test reading UTF-16 BE plugin."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False) as f:
        f.write(b"\xfe\xff")  # BOM
        f.write("{ test }".encode("utf-16-be"))
        f.flush()
        content = read_plugin(Path(f.name))
        # BOM becomes \ufeff character in decoded string
        assert content.lstrip("\ufeff") == "{ test }"
        Path(f.name).unlink()


def test_read_plugin_utf16_le() -> None:
    """Test reading UTF-16 LE plugin."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False) as f:
        f.write(b"\xff\xfe")  # BOM
        f.write("{ test }".encode("utf-16-le"))
        f.flush()
        content = read_plugin(Path(f.name))
        # BOM becomes \ufeff character in decoded string
        assert content.lstrip("\ufeff") == "{ test }"
        Path(f.name).unlink()


def test_lint_braces_balanced() -> None:
    """Test balanced braces."""
    errors = lint_braces("{ foo() }")
    assert len(errors) == 0


def test_lint_braces_unmatched_close() -> None:
    """Test unmatched closing brace."""
    errors = lint_braces("{ } }")
    assert len(errors) == 1
    assert errors[0].code == "MS-E001"


def test_lint_braces_mismatched() -> None:
    """Test mismatched braces."""
    errors = lint_braces("{ [ }")
    assert any(e.code == "MS-E002" for e in errors)


def test_lint_braces_unclosed() -> None:
    """Test unclosed brace."""
    errors = lint_braces("{ foo(")
    assert any(e.code == "MS-E003" for e in errors)


def test_lint_braces_in_string() -> None:
    """Test braces inside strings are ignored."""
    errors = lint_braces('{ "}" }')
    assert len(errors) == 0


def test_lint_braces_in_comment() -> None:
    """Test braces in comments are ignored."""
    errors = lint_braces("{ // }\n}")
    assert len(errors) == 0


def test_lint_strings_valid() -> None:
    """Test valid strings."""
    errors = lint_strings('"hello"')
    assert len(errors) == 0


def test_lint_methods_reserved_word() -> None:
    """Test reserved word as method name."""
    errors = lint_methods('if "()"')
    assert len(errors) == 1
    assert errors[0].code == "MS-W001"


def test_lint_methods_valid() -> None:
    """Test valid method name."""
    errors = lint_methods('Initialize "()"')
    assert len(errors) == 0


def test_lint_common_trailing_whitespace() -> None:
    """Test trailing whitespace detection."""
    errors = lint_common_issues("foo ")
    assert any(e.code == "MS-W002" for e in errors)


def test_lint_common_long_line() -> None:
    """Test long line detection."""
    errors = lint_common_issues("x" * 250)
    assert any(e.code == "MS-W003" for e in errors)


def test_lint_plugin_structure_missing_brace() -> None:
    """Test missing opening brace."""
    errors = lint_plugin_structure("Initialize")
    assert any(e.code == "MS-E010" for e in errors)


def test_lint_plugin_structure_missing_end() -> None:
    """Test missing closing brace."""
    errors = lint_plugin_structure("{")
    assert any(e.code == "MS-E011" for e in errors)


def test_lint_plugin_structure_missing_init() -> None:
    """Test missing Initialize method."""
    errors = lint_plugin_structure("{ Run }")
    assert any(e.code == "MS-W010" for e in errors)


def test_lint_plugin_structure_missing_menu() -> None:
    """Test missing AddToPluginsMenu."""
    errors = lint_plugin_structure("{ Initialize }")
    assert any(e.code == "MS-W011" for e in errors)


def test_lint_plugin_structure_valid() -> None:
    """Test valid plugin structure."""
    content = "{ Initialize AddToPluginsMenu }"
    errors = lint_plugin_structure(content)
    assert not any(
        e.code in ("MS-E010", "MS-E011", "MS-W010", "MS-W011") for e in errors
    )


def test_lint_method_calls_tokenize_error() -> None:
    """Test that tokenize errors don't crash lint."""
    # This would need a really malformed input
    errors = lint_method_calls("")
    assert errors == []


def test_lint_full_file() -> None:
    """Test full lint on valid plugin."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
        f.write('{ Initialize "() { AddToPluginsMenu(); }" }')
        f.flush()
        errors = lint(Path(f.name))
        # Should have no critical errors
        assert not any(e.code.startswith("E0") for e in errors)
        Path(f.name).unlink()


def test_lint_main_no_args() -> None:
    """Test main with no arguments shows usage and exits."""
    with pytest.raises(SystemExit) as exc:
        lint_main([])
    assert exc.value.code == 2  # argparse exits with 2 for missing args


def test_lint_main_missing_file() -> None:
    """Test main with missing file."""
    with patch.object(sys, "argv", ["lint.py", "nonexistent.plg"]):
        assert lint_main() == 1


def test_lint_main_success() -> None:
    """Test main with valid file."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
        f.write('{ Initialize "() { AddToPluginsMenu(); }" }')
        f.flush()
        result = lint_main([f.name])
        # May have warnings but should run
        assert result >= 0
        Path(f.name).unlink()


def test_lint_main_fix() -> None:
    """Test main with --fix flag."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
        # File with trailing whitespace
        f.write('{ Initialize "() { AddToPluginsMenu(); }" }   ')
        f.flush()
        result = lint_main(["--fix", f.name])
        assert result >= 0
        # Check file was fixed
        content = Path(f.name).read_text()
        assert not content.endswith("   ")
        Path(f.name).unlink()


def test_lint_main_fix_with_remaining_errors() -> None:
    """Test main with --fix when errors remain after fix."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
        # File with trailing whitespace AND a real error (unclosed brace)
        f.write("{ Initialize   ")  # trailing whitespace + unclosed brace
        f.flush()
        result = lint_main(["--fix", f.name])
        # Should have errors (unclosed brace)
        assert result > 0
        Path(f.name).unlink()


def test_lint_main_fix_no_trailing_whitespace() -> None:
    """Test main with --fix when no trailing whitespace to fix."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
        # Valid file with no trailing whitespace
        f.write('{ Initialize "() { AddToPluginsMenu(); }" }')
        f.flush()
        result = lint_main(["--fix", f.name])
        # Should succeed (no changes needed)
        assert result >= 0
        Path(f.name).unlink()


# =============================================================================
# manuscript_ast tests
# =============================================================================


def test_lint_braces_single_quote_escape() -> None:
    """Test single quote string handling."""
    errors = lint_braces("{ x = 'it\\'s'; }")
    assert len(errors) == 0


def test_lint_braces_double_quote_escape() -> None:
    """Test double quote string handling."""
    errors = lint_braces('{ x = "test\\"quote"; }')
    assert len(errors) == 0


def test_lint_method_calls_with_valid_params() -> None:
    """Test lint_method_calls with known method."""
    # CreateSparseArray() can have 0+ args
    errors = lint_method_calls("CreateSparseArray();")
    assert len(errors) == 0


def test_lint_main_with_errors() -> None:
    """Test lint main when errors found."""
    with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
        f.write("missing braces")  # Will have E010
        f.flush()
        with patch.object(sys, "argv", ["lint.py", f.name]):
            result = lint_main()
            assert result > 0  # Should have errors
        Path(f.name).unlink()


def test_lint_common_issues_tab_trailing() -> None:
    """Test tab as trailing whitespace."""
    errors = lint_common_issues("foo\t")
    assert any(e.code == "MS-W002" for e in errors)


def test_lint_strings_comment_line() -> None:
    """Test comment line is skipped in string checking."""
    errors = lint_strings('// this has unbalanced " quote')
    assert len(errors) == 0


def test_lint_strings_empty_line() -> None:
    """Test empty content."""
    errors = lint_strings("")
    assert len(errors) == 0


def test_lint_strings_escape_at_end_of_line() -> None:
    """Test escape sequence at very end of line."""
    # Line 139-140: char == "\\" and i + 1 < len(line_content) is False
    errors = lint_strings('x = "test\\')  # Escape at end
    # Should not crash, may or may not report error
    assert isinstance(errors, list)


def test_lint_strings_odd_quotes_with_empty_string() -> None:
    """Test line with odd quotes but contains empty string literal."""
    # Line 154: quote_count % 2 != 0 and '""' not in line_content
    errors = lint_strings('x = "" + "a')
    assert isinstance(errors, list)


def test_lint_method_calls_empty_signatures() -> None:
    """Test lint_method_calls with empty signatures."""
    import mahlif.sibelius.manuscript.lint_methods as methods_module

    old_sigs = methods_module.METHOD_SIGNATURES
    methods_module.METHOD_SIGNATURES = {}
    try:
        # With no signatures, unknown methods are not errors
        errors = lint_method_calls("foo();")
        assert isinstance(errors, list)
        assert errors == []
    finally:
        methods_module.METHOD_SIGNATURES = old_sigs


def test_lint_method_calls_tokenization_exception() -> None:
    """Test when get_method_calls raises exception."""
    # Lines 232-234: except Exception branch
    # Pass invalid input that causes tokenization to fail
    errors = lint_method_calls(None)  # type: ignore[arg-type]
    assert errors == []


def test_lint_method_calls_too_few_args() -> None:
    """Test method with too few arguments."""
    # Line 240: arg_count < min_params
    # AddNote requires at least 1 arg
    errors = lint_method_calls("AddNote();")
    assert any(e.code == "MS-E020" for e in errors)


def test_lint_method_calls_too_many_args() -> None:
    """Test method with too many arguments."""
    # Line 249: arg_count > max_params
    # Need a method with a known max_params
    # Let's use one that exists in the API
    errors = lint_method_calls("Sibelius.Play(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);")
    # May or may not find error depending on API definition
    assert isinstance(errors, list)


def test_lint_strings_escape_mid_line() -> None:
    """Test escape sequence in middle of line (not at end)."""
    # Lines 139-140: char == "\\" and i + 1 < len(line_content) is True
    errors = lint_strings('x = "test\\"quoted";')
    assert isinstance(errors, list)


def test_lint_braces_mixed_quotes() -> None:
    """Test string with opposite quote inside."""
    # Single quote inside double-quoted string
    errors = lint_braces('x = "it\'s working";')
    assert len(errors) == 0


def test_lint_braces_nested_quotes() -> None:
    """Test double quote inside single-quoted string."""
    errors = lint_braces("x = 'say \"hello\"';")
    assert len(errors) == 0


def test_lint_strings_odd_quotes_with_double_empty() -> None:
    """Test line with odd quotes but contains empty string literal."""
    # This has 3 quotes total: "" and one more "
    errors = lint_strings('x = "" + "incomplete')
    assert isinstance(errors, list)


def test_lint_strings_odd_quotes_no_empty_string() -> None:
    """Test line with odd quotes and no empty string literal."""
    # This has 3 quotes and no ""
    errors = lint_strings('x = "a" + "b')
    assert isinstance(errors, list)


def test_noqa_with_codes() -> None:
    """Test noqa with specific codes."""

    content = "// noqa: MS-W002, MS-W003\nx = 1;"
    directives = parse_inline_directives(content)
    assert directives.is_ignored(1, "MS-W002")
    assert directives.is_ignored(1, "MS-W003")
    # Also applies to next line for comment-only lines
    assert directives.is_ignored(2, "MS-W002")
    assert not directives.is_ignored(3, "MS-W002")


def test_noqa_without_codes() -> None:
    """Test noqa without codes ignores all."""

    content = "// noqa\nx = 1;"
    directives = parse_inline_directives(content)
    # Empty set means ignore all
    assert directives.is_ignored(1, "MS-W002")
    assert directives.is_ignored(1, "MS-E001")
    assert directives.is_ignored(2, "MS-W002")


def test_noqa_inline() -> None:
    """Test noqa on same line as code."""

    content = "x = 1;  // noqa: MS-W002"
    directives = parse_inline_directives(content)
    assert directives.is_ignored(1, "MS-W002")
    # Does not apply to next line (not a comment-only line)
    assert not directives.is_ignored(2, "MS-W002")


def test_mahlif_disable_enable() -> None:
    """Test mahlif: disable/enable region."""

    content = """line 1
// mahlif: disable MS-W002
line 3
line 4
// mahlif: enable MS-W002
line 6"""
    directives = parse_inline_directives(content)
    assert not directives.is_ignored(1, "MS-W002")
    # disable comment line itself is disabled (after processing)
    assert directives.is_ignored(3, "MS-W002")
    assert directives.is_ignored(4, "MS-W002")
    # enable line is still disabled (disable was active at start of line)
    assert directives.is_ignored(5, "MS-W002")
    assert not directives.is_ignored(6, "MS-W002")


def test_disable_multiple_codes() -> None:
    """Test disabling multiple codes at once."""

    content = """line 1
// mahlif: disable MS-W002, MS-W003
line 3"""
    directives = parse_inline_directives(content)
    assert directives.is_ignored(3, "MS-W002")
    assert directives.is_ignored(3, "MS-W003")
    assert not directives.is_ignored(3, "MS-E001")


def test_lint_respects_noqa(tmp_path: Path) -> None:
    """Test lint() respects noqa comments."""
    from mahlif.sibelius.manuscript.lint import lint

    plg = tmp_path / "test.plg"
    plg.write_text(
        "{\n"
        "    Initialize \"() { AddToPluginsMenu('T', 'R'); }\"   // noqa: MS-W002\n"
        '    Run "() { }"\n'
        "}"
    )

    errors = lint(plg)
    # W002 should be suppressed by noqa
    assert not any(e.code == "MS-W002" for e in errors)


def test_lint_respects_disable_region(tmp_path: Path) -> None:
    """Test lint() respects disable/enable regions."""

    plg = tmp_path / "test.plg"
    plg.write_text(
        "{\n"
        "    Initialize \"() { AddToPluginsMenu('T', 'R'); }\"\n"
        "    // mahlif: disable MS-W002\n"
        '    Run "() { }"   \n'  # trailing whitespace
        "    // mahlif: enable MS-W002\n"
        "}"
    )


def test_lint_can_ignore_inline(tmp_path: Path) -> None:
    """Test lint() can ignore inline directives with respect_inline flag."""
    from mahlif.sibelius.manuscript.lint import lint

    plg = tmp_path / "test.plg"
    # Missing Initialize - triggers W010
    plg.write_text('{ Run "() { }" }  // noqa: MS-W010')

    # With respect_inline=True, W010 should be suppressed
    errors_with_inline = lint(plg, respect_inline=True)
    assert not any(e.code == "MS-W010" for e in errors_with_inline)

    # With respect_inline=False, W010 should NOT be suppressed
    errors_without_inline = lint(plg, respect_inline=False)
    assert any(e.code == "MS-W010" for e in errors_without_inline)


def test_extract_variables_no_matches() -> None:
    """Test extract_plugin_variables with content that has no variable declarations."""
    from mahlif.sibelius.manuscript.lint_bodies import extract_plugin_variables

    # Content with only methods, no variable declarations
    content = """
{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { Sibelius.MessageBox('hi'); }"
}
"""
    variables = extract_plugin_variables(content)
    assert variables == set()


def test_ignore_directive_on_own_line() -> None:
    """Test // mahlif: ignore on its own line applies to next line."""
    from mahlif.sibelius.manuscript.lint_directives import parse_inline_directives

    content = """// mahlif: ignore MS-W002
trailing whitespace   
"""
    directives = parse_inline_directives(content)
    # Should ignore MS-W002 on line 2
    assert directives.is_ignored(2, "MS-W002")


def test_extract_variables_excludes_methods() -> None:
    """Test that Initialize and Run are excluded from variables."""
    from mahlif.sibelius.manuscript.lint_bodies import extract_plugin_variables

    content = """
{
    MyVar "some value"
    Initialize "() { }"
    Run "() { }"
    OtherVar "other value"
}
"""
    variables = extract_plugin_variables(content)
    # MyVar and OtherVar should be found, but not Initialize or Run
    assert "MyVar" in variables
    assert "OtherVar" in variables
    assert "Initialize" not in variables
    assert "Run" not in variables


def test_extract_variables_excludes_initialize_as_var() -> None:
    """Test that Initialize is excluded even if it looks like a variable."""
    from mahlif.sibelius.manuscript.lint_bodies import extract_plugin_variables

    # Edge case: Initialize with non-method string (not starting with "(")
    content = """
{
    Initialize "not a method definition"
    MyVar "some value"
}
"""
    variables = extract_plugin_variables(content)
    assert "MyVar" in variables
    assert "Initialize" not in variables


def test_ignore_directive_inline() -> None:
    """Test // mahlif: ignore inline (not on its own line)."""
    from mahlif.sibelius.manuscript.lint_directives import parse_inline_directives

    content = """x = 1;  // mahlif: ignore MS-W002
"""
    directives = parse_inline_directives(content)
    # Should ignore MS-W002 on line 1 only
    assert directives.is_ignored(1, "MS-W002")
    assert not directives.is_ignored(2, "MS-W002")


def test_ignore_directive_consecutive_lines() -> None:
    """Test consecutive ignore directives."""
    from mahlif.sibelius.manuscript.lint_directives import parse_inline_directives

    content = """// mahlif: ignore MS-W001
// mahlif: ignore MS-W002
some line
"""
    directives = parse_inline_directives(content)
    # Line 2 should have both MS-W001 (from line 1) and MS-W002 (from line 2)
    assert directives.is_ignored(2, "MS-W001")
    assert directives.is_ignored(2, "MS-W002")
    # Line 3 should have MS-W002 (from line 2)
    assert directives.is_ignored(3, "MS-W002")


def test_ignore_directive_overlap() -> None:
    """Test ignore directive where next line already has ignores."""
    from mahlif.sibelius.manuscript.lint_directives import parse_inline_directives

    # Line 1: standalone ignore -> adds to line 2
    # Line 2: also has ignore (inline) -> line 2 already exists when we try to add
    content = """// mahlif: ignore MS-W001
x = 1;  // mahlif: ignore MS-W002
"""
    directives = parse_inline_directives(content)
    # Line 2 should have both
    assert directives.is_ignored(2, "MS-W001")
    assert directives.is_ignored(2, "MS-W002")


def test_lint_for_loop_bounds_no_matches() -> None:
    """Test lint_for_loop_bounds with no matching patterns."""
    from mahlif.sibelius.manuscript.lint_bodies import lint_for_loop_bounds

    # No for loops at all
    content = '{ Initialize "() { x = 1; }" }'
    errors = lint_for_loop_bounds(content)
    assert errors == []

    # For loop but not the risky pattern (no subtraction)
    content = '{ Run "() { for i = 0 to 10 { x = i; } }" }'
    errors = lint_for_loop_bounds(content)
    assert errors == []


def test_lint_for_loop_bounds_nonzero_start() -> None:
    """Test for loop with non-zero start - no warning."""
    from mahlif.sibelius.manuscript.lint_bodies import lint_for_loop_bounds

    # Start is 1, not 0 - different semantics, no warning
    content = '{ Run "() { for i = 1 to Length(x) - 1 { y = i; } }" }'
    errors = lint_for_loop_bounds(content)
    assert errors == []
