"""Linting for Sibelius ManuScript .plg files.

This module provides comprehensive linting including:
- Plugin structure validation
- Brace matching
- Method definition checking
- API call validation
- Inline directive support (noqa, mahlif: ignore/disable/enable)
- Auto-fix capabilities
"""

from __future__ import annotations

from pathlib import Path

from .errors import LintError
from .lint_bodies import extract_method_bodies
from .lint_bodies import lint_for_loop_bounds
from .lint_bodies import lint_method_bodies
from .lint_braces import lint_braces
from .lint_braces import lint_strings
from .lint_common import lint_common_issues
from .lint_common import read_plugin
from .lint_directives import InlineDirectives
from .lint_directives import parse_inline_directives
from .lint_fix import fix_trailing_whitespace
from .lint_methods import lint_method_calls
from .lint_methods import lint_methods
from .lint_structure import lint_plugin_structure


def lint(path: Path, respect_inline: bool = True) -> list[LintError]:
    """Run all lints on a plugin file.

    Args:
        path: Path to plugin file
        respect_inline: Whether to respect inline noqa/mahlif comments

    Returns:
        List of lint errors, sorted by line and column
    """
    content = read_plugin(path)
    errors: list[LintError] = []

    errors.extend(lint_plugin_structure(content))
    errors.extend(lint_braces(content))
    errors.extend(lint_strings(content))
    errors.extend(lint_methods(content))
    errors.extend(lint_method_calls(content))
    errors.extend(lint_common_issues(content))
    errors.extend(lint_method_bodies(content))
    errors.extend(lint_for_loop_bounds(content))

    # Filter out errors suppressed by inline directives
    if respect_inline:
        directives = parse_inline_directives(content)
        errors = [e for e in errors if not directives.is_ignored(e.line, e.code)]

    # Sort by line, then column
    errors.sort(key=lambda e: (e.line, e.col))
    return errors


def main(args: list[str] | None = None) -> int:
    """Main entry point for lint CLI.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success)
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Lint Sibelius ManuScript .plg files")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix trailing whitespace",
    )
    parser.add_argument(
        "files",
        type=Path,
        nargs="+",
        help="Plugin files to check",
    )

    parsed = parser.parse_args(args)

    total_errors = 0
    for path in parsed.files:
        if not path.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            total_errors += 1
            continue

        errors = lint(path)

        if parsed.fix:
            if fix_trailing_whitespace(path):
                # Filter out fixed W002 errors
                errors = [e for e in errors if e.code != "MS-W002"]
                print(f"✓ {path}: Fixed trailing whitespace")

        if not errors:
            if not parsed.fix:
                print(f"✓ {path}: No issues found")
        else:
            print(f"✗ {path}: {len(errors)} issue(s) found\n")
            for error in errors:
                print(f"  {error}")
            total_errors += len(errors)

    # Return error count (capped at 127 for exit codes)
    return min(total_errors, 127)


__all__ = [
    # Main function
    "lint",
    "main",
    # Errors
    "LintError",
    # Directives
    "InlineDirectives",
    "parse_inline_directives",
    # Individual linters
    "lint_braces",
    "lint_for_loop_bounds",
    "lint_strings",
    "lint_methods",
    "lint_method_calls",
    "lint_common_issues",
    "lint_plugin_structure",
    "lint_method_bodies",
    # Utilities
    "read_plugin",
    "extract_method_bodies",
    "fix_trailing_whitespace",
]
