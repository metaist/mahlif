"""Brace and string literal checking."""

from __future__ import annotations

from .errors import LintError


def lint_braces(content: str) -> list[LintError]:
    """Check for mismatched braces.

    Checks:
    - Unmatched closing braces (MS-E001)
    - Mismatched brace types (MS-E002)
    - Unclosed braces (MS-E003)

    Args:
        content: Plugin file content

    Returns:
        List of lint errors
    """
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
    """Check for unclosed string literals.

    Note: ManuScript allows multi-line strings for method bodies,
    so this is conservative and may not catch all issues.

    Args:
        content: Plugin file content

    Returns:
        List of lint errors (currently empty - too many false positives)
    """
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
