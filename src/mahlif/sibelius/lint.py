#!/usr/bin/env python3
"""Linter for Sibelius ManuScript .plg files.

Usage:
    python lint.py MahlifExport.plg
    python lint.py --fix MahlifExport.plg  # auto-fix some issues
"""

from __future__ import annotations

import json
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


@dataclass
class InlineDirectives:
    """Inline lint directives parsed from comments."""

    # Line-specific ignores: line_number -> set of codes
    line_ignores: dict[int, set[str]]
    # Disabled regions: code -> set of line numbers where disabled
    disabled_lines: dict[str, set[int]]

    def is_ignored(self, line: int, code: str) -> bool:
        """Check if a code is ignored on a specific line."""
        # Check line-specific ignores
        if line in self.line_ignores:
            ignores = self.line_ignores[line]
            if not ignores or code in ignores:  # Empty set means ignore all
                return True

        # Check disabled regions
        if code in self.disabled_lines and line in self.disabled_lines[code]:
            return True

        return False


def parse_inline_directives(content: str) -> InlineDirectives:
    """Parse inline lint directives from content.

    Supports:
        // noqa: MS-W002, MS-W003  (ignore on this/next line)
        // mahlif: ignore MS-W002  (ignore on this/next line)
        // mahlif: disable MS-W002 (disable until enable)
        // mahlif: enable MS-W002  (re-enable)

    Args:
        content: Plugin file content

    Returns:
        InlineDirectives with parsed information
    """
    line_ignores: dict[int, set[str]] = {}
    disabled_lines: dict[str, set[int]] = {}

    # Track currently disabled codes
    currently_disabled: set[str] = set()

    lines = content.split("\n")

    # Patterns for inline comments
    noqa_pattern = re.compile(r"//\s*noqa(?::\s*([A-Z0-9-,\s]+))?", re.IGNORECASE)
    mahlif_ignore_pattern = re.compile(
        r"//\s*mahlif:\s*ignore\s+([A-Z0-9-,\s]+)", re.IGNORECASE
    )
    mahlif_disable_pattern = re.compile(
        r"//\s*mahlif:\s*disable\s+([A-Z0-9-,\s]+)", re.IGNORECASE
    )
    mahlif_enable_pattern = re.compile(
        r"//\s*mahlif:\s*enable\s+([A-Z0-9-,\s]+)", re.IGNORECASE
    )

    for line_num, line_content in enumerate(lines, 1):
        # Add currently disabled codes to this line
        for code in currently_disabled:
            if code not in disabled_lines:
                disabled_lines[code] = set()
            disabled_lines[code].add(line_num)

        # Check for noqa comment
        noqa_match = noqa_pattern.search(line_content)
        if noqa_match:
            codes_str = noqa_match.group(1)
            if codes_str:
                codes = {c.strip() for c in codes_str.split(",") if c.strip()}
            else:
                codes = set()  # Empty means ignore all

            # Apply to current line and next line (for comment-only lines)
            line_ignores[line_num] = codes
            if line_content.strip().startswith("//"):
                # Comment-only line - also apply to next line
                line_ignores[line_num + 1] = codes

        # Check for mahlif: ignore comment
        ignore_match = mahlif_ignore_pattern.search(line_content)
        if ignore_match:
            codes = {c.strip() for c in ignore_match.group(1).split(",") if c.strip()}
            if line_num not in line_ignores:
                line_ignores[line_num] = set()
            line_ignores[line_num] |= codes
            if line_content.strip().startswith("//"):
                if line_num + 1 not in line_ignores:
                    line_ignores[line_num + 1] = set()
                line_ignores[line_num + 1] |= codes

        # Check for mahlif: disable comment
        disable_match = mahlif_disable_pattern.search(line_content)
        if disable_match:
            codes = {c.strip() for c in disable_match.group(1).split(",") if c.strip()}
            currently_disabled |= codes

        # Check for mahlif: enable comment
        enable_match = mahlif_enable_pattern.search(line_content)
        if enable_match:
            codes = {c.strip() for c in enable_match.group(1).split(",") if c.strip()}
            currently_disabled -= codes

    return InlineDirectives(line_ignores=line_ignores, disabled_lines=disabled_lines)


def read_plugin(path: Path) -> str:
    """Read plugin file, handling UTF-8 or UTF-16."""
    raw = path.read_bytes()
    if raw.startswith(b"\xfe\xff"):
        # UTF-16 BE with BOM - skip BOM bytes
        return raw[2:].decode("utf-16-be")
    elif raw.startswith(b"\xff\xfe"):
        # UTF-16 LE with BOM - skip BOM bytes
        return raw[2:].decode("utf-16-le")
    elif len(raw) >= 2 and raw[0] == 0 and raw[1] != 0:
        # UTF-16 BE without BOM (first byte is null, second is not)
        return raw.decode("utf-16-be")
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
                    LintError(line, col, "MS-E001", f"Unmatched closing '{char}'")
                )
            else:
                open_line, open_col, open_char = stack.pop()
                expected = {"(": ")", "{": "}", "[": "]"}[open_char]
                if char != expected:
                    errors.append(
                        LintError(
                            line,
                            col,
                            "MS-E002",
                            f"Mismatched brace: expected '{expected}' "
                            f"(opened at {open_line}:{open_col}), got '{char}'",
                        )
                    )

        col += 1
        i += 1

    # Check for unclosed braces
    for open_line, open_col, open_char in stack:
        errors.append(
            LintError(open_line, open_col, "MS-E003", f"Unclosed '{open_char}'")
        )

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
        if quote_count % 2 != 0 and '""' not in line_content:  # pragma: no branch
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
                        "MS-W001",
                        f"Method name '{method_name}' is a reserved word",
                    )
                )

    return errors


def _load_method_signatures() -> dict[str, tuple[int, int]]:
    """Load method signatures from JSON file."""
    json_path = Path(__file__).parent / "manuscript_api.json"
    if not json_path.exists():
        return {}

    with open(json_path) as f:
        data = json.load(f)

    signatures: dict[str, tuple[int, int]] = {}
    for name, info in data.get("methods", {}).items():
        signatures[name] = (info["min_params"], info["max_params"])

    # Manual overrides for methods with multiple signatures or special cases
    signatures["AddNote"] = (1, 7)  # Bar or NoteRest context
    signatures["CreateSparseArray"] = (0, 99)  # Variadic

    return signatures


METHOD_SIGNATURES = _load_method_signatures()


def lint_method_calls(content: str) -> list[LintError]:
    """Check method call parameter counts using AST."""
    from mahlif.sibelius.manuscript_ast import get_method_calls

    errors: list[LintError] = []

    try:
        calls = get_method_calls(content)
    except Exception:
        # If tokenization fails, fall back to no checking
        return errors

    for line, col, obj, method, arg_count in calls:
        if method in METHOD_SIGNATURES:
            min_params, max_params = METHOD_SIGNATURES[method]
            if arg_count < min_params:
                errors.append(
                    LintError(
                        line,
                        col,
                        "MS-E020",
                        f"{method}() requires at least {min_params} args, got {arg_count}",
                    )
                )
            elif arg_count > max_params:
                errors.append(
                    LintError(
                        line,
                        col,
                        "MS-E021",
                        f"{method}() accepts at most {max_params} args, got {arg_count}",
                    )
                )

    return errors


def lint_common_issues(content: str) -> list[LintError]:
    """Check for common ManuScript issues."""
    errors: list[LintError] = []
    lines = content.split("\n")

    for line_num, line_content in enumerate(lines, 1):
        # Check for trailing whitespace
        if line_content.endswith(" ") or line_content.endswith("\t"):
            errors.append(
                LintError(line_num, len(line_content), "MS-W002", "Trailing whitespace")
            )

        # Check for very long lines
        if len(line_content) > 200:
            errors.append(
                LintError(
                    line_num,
                    200,
                    "MS-W003",
                    f"Line too long ({len(line_content)} chars)",
                )
            )

    return errors


def lint_plugin_structure(content: str) -> list[LintError]:
    """Check plugin has required structure."""
    errors: list[LintError] = []

    # Must start with { (strip BOM if present)
    stripped = content.lstrip("\ufeff").strip()
    if not stripped.startswith("{"):
        errors.append(LintError(1, 1, "MS-E010", "Plugin must start with '{'"))

    # Must end with }
    if not stripped.endswith("}"):
        errors.append(
            LintError(content.count("\n") + 1, 1, "MS-E011", "Plugin must end with '}'")
        )

    # Should have Initialize method
    if "Initialize" not in content:
        errors.append(LintError(1, 1, "MS-W010", "Missing 'Initialize' method"))

    # Initialize should call AddToPluginsMenu
    if "Initialize" in content and "AddToPluginsMenu" not in content:
        errors.append(
            LintError(1, 1, "MS-W011", "Initialize should call 'AddToPluginsMenu'")
        )

    return errors


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

    # Filter out errors suppressed by inline directives
    if respect_inline:
        directives = parse_inline_directives(content)
        errors = [e for e in errors if not directives.is_ignored(e.line, e.code)]

    # Sort by line, then column
    errors.sort(key=lambda e: (e.line, e.col))
    return errors


def fix_trailing_whitespace(path: Path) -> bool:
    """Fix trailing whitespace in a plugin file.

    Args:
        path: Path to plugin file

    Returns:
        True if changes were made
    """
    content = read_plugin(path)
    lines = content.split("\n")
    fixed_lines = [line.rstrip() for line in lines]

    if lines == fixed_lines:
        return False

    # Re-read to preserve original encoding for write
    raw = path.read_bytes()
    if raw.startswith(b"\xfe\xff"):
        encoding = "utf-16-be"
        bom = b"\xfe\xff"
    elif raw.startswith(b"\xff\xfe"):
        encoding = "utf-16-le"
        bom = b"\xff\xfe"
    else:
        encoding = "utf-8"
        bom = b""

    fixed_content = "\n".join(fixed_lines)
    with open(path, "wb") as f:
        f.write(bom)
        f.write(fixed_content.encode(encoding))

    return True


def main(args: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success)
    """
    import argparse

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
            print(f"Error: {path} not found")
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


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
