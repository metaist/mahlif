"""Auto-fix capabilities for linting."""

from __future__ import annotations

from pathlib import Path

from .lint_common import read_plugin


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
