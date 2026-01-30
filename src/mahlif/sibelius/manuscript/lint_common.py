"""Common utilities and checks for linting."""

from __future__ import annotations

from pathlib import Path

from .errors import LintError


def read_plugin(path: Path) -> str:
    """Read plugin file, handling UTF-8 or UTF-16.

    Args:
        path: Path to plugin file

    Returns:
        File content as string
    """
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


def lint_common_issues(content: str) -> list[LintError]:
    """Check for common ManuScript issues.

    Checks:
    - Trailing whitespace (MS-W002)
    - Very long lines (MS-W003)

    Args:
        content: Plugin file content

    Returns:
        List of lint errors
    """
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
