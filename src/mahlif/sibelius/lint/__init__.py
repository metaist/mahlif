"""Backwards compatibility - linting moved to manuscript package.

Import from mahlif.sibelius.manuscript.lint instead.
"""

from __future__ import annotations

# Re-export everything from the new location
from mahlif.sibelius.manuscript.lint import InlineDirectives
from mahlif.sibelius.manuscript.lint import LintError
from mahlif.sibelius.manuscript.lint import extract_method_bodies
from mahlif.sibelius.manuscript.lint import fix_trailing_whitespace
from mahlif.sibelius.manuscript.lint import lint
from mahlif.sibelius.manuscript.lint import lint_braces
from mahlif.sibelius.manuscript.lint import lint_common_issues
from mahlif.sibelius.manuscript.lint import lint_method_bodies
from mahlif.sibelius.manuscript.lint import lint_method_calls
from mahlif.sibelius.manuscript.lint import lint_methods
from mahlif.sibelius.manuscript.lint import lint_plugin_structure
from mahlif.sibelius.manuscript.lint import lint_strings
from mahlif.sibelius.manuscript.lint import main
from mahlif.sibelius.manuscript.lint import parse_inline_directives
from mahlif.sibelius.manuscript.lint import read_plugin

__all__ = [
    "lint",
    "main",
    "LintError",
    "InlineDirectives",
    "parse_inline_directives",
    "lint_braces",
    "lint_strings",
    "lint_methods",
    "lint_method_calls",
    "lint_common_issues",
    "lint_plugin_structure",
    "lint_method_bodies",
    "read_plugin",
    "extract_method_bodies",
    "fix_trailing_whitespace",
]
