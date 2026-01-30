"""Plugin structure validation."""

from __future__ import annotations

import re

from .errors import LintError


def lint_plugin_structure(content: str) -> list[LintError]:
    """Check plugin has required structure.

    Checks:
    - Plugin must start with '{' (MS-E010)
    - Plugin must end with '}' (MS-E011)
    - Should have Initialize method (MS-W010)
    - Initialize should call AddToPluginsMenu (MS-W011)

    Args:
        content: Plugin file content

    Returns:
        List of lint errors
    """
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

    # Check for duplicate method definitions
    errors.extend(_lint_duplicate_methods(content))

    return errors


def _lint_duplicate_methods(content: str) -> list[LintError]:
    """Check for duplicate method definitions.

    Args:
        content: Plugin file content

    Returns:
        List of lint errors for duplicate methods
    """
    errors: list[LintError] = []

    # Pattern: MethodName "..." at start of line (with optional whitespace)
    # This matches member definitions like: Initialize "() { ... }"
    method_pattern = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s+"', re.MULTILINE)

    # Track method definitions: name -> list of (line_num, col)
    method_defs: dict[str, list[tuple[int, int]]] = {}

    for match in method_pattern.finditer(content):
        name = match.group(1)
        # Calculate line number
        line_num = content[: match.start()].count("\n") + 1
        col = match.start() - content.rfind("\n", 0, match.start())

        if name not in method_defs:
            method_defs[name] = []
        method_defs[name].append((line_num, col))

    # Report duplicates
    for name, locations in method_defs.items():
        if len(locations) > 1:
            # Report all but the first occurrence
            for line_num, col in locations[1:]:
                errors.append(
                    LintError(
                        line_num,
                        col,
                        "MS-W027",
                        f"Duplicate method definition '{name}' "
                        f"(first defined at line {locations[0][0]})",
                    )
                )

    return errors
