"""Inline lint directive parsing.

Supports:
    // noqa: MS-W002, MS-W003  (ignore on this/next line)
    // mahlif: ignore MS-W002  (ignore on this/next line)
    // mahlif: disable MS-W002 (disable until enable)
    // mahlif: enable MS-W002  (re-enable)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class InlineDirectives:
    """Inline lint directives parsed from comments."""

    # Line-specific ignores: line_number -> set of codes
    line_ignores: dict[int, set[str]]
    # Disabled regions: code -> set of line numbers where disabled
    disabled_lines: dict[str, set[int]]

    def is_ignored(self, line: int, code: str) -> bool:
        """Check if a code is ignored on a specific line.

        Args:
            line: Line number
            code: Error code

        Returns:
            True if the error should be ignored
        """
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
                # Apply to next line too (standalone comment)
                if line_num + 1 not in line_ignores:  # pragma: no branch
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
