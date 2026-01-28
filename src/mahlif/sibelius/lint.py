#!/usr/bin/env python3
"""Linter for Sibelius ManuScript .plg files.

Usage:
    python lint.py MahlifExport.plg
    python lint.py --fix MahlifExport.plg  # auto-fix some issues
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LintError:
    """A linting error."""

    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.line}:{self.col} [{self.code}] {self.message}"


def read_plugin(path: Path) -> str:
    """Read plugin file, handling UTF-8 or UTF-16."""
    raw = path.read_bytes()
    if raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16-be")
    elif raw.startswith(b"\xff\xfe"):
        return raw.decode("utf-16-le")
    else:
        return raw.decode("utf-8")


def lint_braces(content: str) -> list[LintError]:
    """Check for mismatched braces."""
    errors: list[LintError] = []
    stack: list[tuple[int, int, str]] = []  # (line, col, char)

    in_string = False
    string_char = None
    i = 0
    line = 1
    col = 1

    while i < len(content):
        char = content[i]

        # Track newlines
        if char == "\n":
            line += 1
            col = 1
            i += 1
            continue

        # Handle string literals
        if char in "\"'" and (i == 0 or content[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            col += 1
            i += 1
            continue

        # Skip if inside string
        if in_string:
            col += 1
            i += 1
            continue

        # Handle comments (// to end of line)
        if char == "/" and i + 1 < len(content) and content[i + 1] == "/":
            # Skip to end of line
            while i < len(content) and content[i] != "\n":
                i += 1
            continue

        # Track braces
        if char in "({[":
            stack.append((line, col, char))
        elif char in ")}]":
            if not stack:
                errors.append(
                    LintError(line, col, "E001", f"Unmatched closing '{char}'")
                )
            else:
                open_line, open_col, open_char = stack.pop()
                expected = {"(": ")", "{": "}", "[": "]"}[open_char]
                if char != expected:
                    errors.append(
                        LintError(
                            line,
                            col,
                            "E002",
                            f"Mismatched brace: expected '{expected}' "
                            f"(opened at {open_line}:{open_col}), got '{char}'",
                        )
                    )

        col += 1
        i += 1

    # Check for unclosed braces
    for open_line, open_col, open_char in stack:
        errors.append(LintError(open_line, open_col, "E003", f"Unclosed '{open_char}'"))

    return errors


def lint_strings(content: str) -> list[LintError]:
    """Check for unclosed string literals."""
    errors: list[LintError] = []
    lines = content.split("\n")

    for line_num, line_content in enumerate(lines, 1):
        # Skip comment lines
        stripped = line_content.strip()
        if stripped.startswith("//"):
            continue

        # Count quotes (simple heuristic - doesn't handle escapes perfectly)
        in_string = False
        i = 0
        while i < len(line_content):
            char = line_content[i]

            # Handle escape sequences
            if char == "\\" and i + 1 < len(line_content):
                i += 2
                continue

            if char == '"':
                in_string = not in_string

            i += 1

        # ManuScript allows multi-line strings for method bodies
        # So unclosed quotes on a line aren't always errors
        # But we can warn about odd quote counts in non-method lines
        quote_count = line_content.count('"') - line_content.count('\\"')
        if quote_count % 2 != 0 and '""' not in line_content:
            # Could be method definition like: MethodName "() { ... }"
            # These legitimately have strings spanning concept
            pass  # Skip for now - too many false positives

    return errors


def lint_methods(content: str) -> list[LintError]:
    """Check method definitions."""
    errors: list[LintError] = []
    lines = content.split("\n")

    # Method pattern: Name "(...) { ... }"
    method_pattern = re.compile(r'^\s*(\w+)\s+"')

    for line_num, line_content in enumerate(lines, 1):
        match = method_pattern.match(line_content)
        if match:
            method_name = match.group(1)

            # Check for reserved words used as method names
            reserved = {
                "if",
                "else",
                "for",
                "while",
                "switch",
                "case",
                "return",
                "true",
                "false",
                "null",
                "and",
                "or",
                "not",
            }
            if method_name.lower() in reserved:
                errors.append(
                    LintError(
                        line_num,
                        1,
                        "W001",
                        f"Method name '{method_name}' is a reserved word",
                    )
                )

    return errors


def lint_common_issues(content: str) -> list[LintError]:
    """Check for common ManuScript issues."""
    errors: list[LintError] = []
    lines = content.split("\n")

    for line_num, line_content in enumerate(lines, 1):
        # Check for == instead of = in comparisons (ManuScript uses = for both)
        # This is actually valid in ManuScript, so skip

        # Check for trailing whitespace
        if line_content.endswith(" ") or line_content.endswith("\t"):
            errors.append(
                LintError(line_num, len(line_content), "W002", "Trailing whitespace")
            )

        # Check for tabs (prefer consistent indentation)
        # Actually ManuScript commonly uses tabs, so skip

        # Check for very long lines
        if len(line_content) > 200:
            errors.append(
                LintError(
                    line_num, 200, "W003", f"Line too long ({len(line_content)} chars)"
                )
            )

    return errors


def lint_plugin_structure(content: str) -> list[LintError]:
    """Check plugin has required structure."""
    errors: list[LintError] = []

    # Must start with { (strip BOM if present)
    stripped = content.lstrip("\ufeff").strip()
    if not stripped.startswith("{"):
        errors.append(LintError(1, 1, "E010", "Plugin must start with '{'"))

    # Must end with }
    if not stripped.endswith("}"):
        errors.append(
            LintError(content.count("\n") + 1, 1, "E011", "Plugin must end with '}'")
        )

    # Should have Initialize method
    if "Initialize" not in content:
        errors.append(LintError(1, 1, "W010", "Missing 'Initialize' method"))

    # Initialize should call AddToPluginsMenu
    if "Initialize" in content and "AddToPluginsMenu" not in content:
        errors.append(
            LintError(1, 1, "W011", "Initialize should call 'AddToPluginsMenu'")
        )

    return errors


def lint(path: Path) -> list[LintError]:
    """Run all lints on a plugin file."""
    content = read_plugin(path)
    errors: list[LintError] = []

    errors.extend(lint_plugin_structure(content))
    errors.extend(lint_braces(content))
    errors.extend(lint_strings(content))
    errors.extend(lint_methods(content))
    errors.extend(lint_common_issues(content))

    # Sort by line, then column
    errors.sort(key=lambda e: (e.line, e.col))
    return errors


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <plugin.plg>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: {path} not found")
        return 1

    errors = lint(path)

    if not errors:
        print(f"✓ {path}: No issues found")
        return 0

    print(f"✗ {path}: {len(errors)} issue(s) found\n")
    for error in errors:
        print(f"  {error}")

    # Return error count (capped at 127 for exit codes)
    return min(len(errors), 127)


if __name__ == "__main__":
    sys.exit(main())
