"""Plugin structure validation."""

from __future__ import annotations

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

    return errors
