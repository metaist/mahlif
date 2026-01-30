"""Method definition and call checking."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .errors import LintError


def lint_methods(content: str) -> list[LintError]:
    """Check method definitions.

    Checks:
    - Reserved words used as method names (MS-W001)

    Args:
        content: Plugin file content

    Returns:
        List of lint errors
    """
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
    """Load method signatures from lang.json.

    For methods that exist on multiple objects with different signatures,
    we use the most permissive range (min of mins, max of maxes).

    Returns:
        Dict mapping method name to (min_params, max_params)
    """
    json_path = Path(__file__).parent.parent / "manuscript" / "lang.json"
    if not json_path.exists():  # pragma: no cover - lang.json is always present
        return {}

    with open(json_path) as f:
        data = json.load(f)

    signatures: dict[str, tuple[int, int]] = {}

    # Collect signatures from all objects
    for obj_info in data.get("objects", {}).values():
        for method_name, method_info in obj_info.get("methods", {}).items():
            for sig in method_info.get("signatures", []):
                min_p = sig.get("min_params", 0)
                max_p = sig.get("max_params", 0)
                if method_name not in signatures:
                    signatures[method_name] = (min_p, max_p)
                else:
                    # Use most permissive range
                    old_min, old_max = signatures[method_name]
                    signatures[method_name] = (min(old_min, min_p), max(old_max, max_p))

    # Also add built-in functions
    for func_name, func_info in data.get("builtin_functions", {}).items():
        params = func_info.get("params", [])
        required = len([p for p in params if not str(p).endswith("?")])
        signatures[func_name] = (required, len(params))

    # Manual overrides for variadic functions
    signatures["CreateSparseArray"] = (0, 99)

    return signatures


METHOD_SIGNATURES = _load_method_signatures()


def lint_method_calls(content: str) -> list[LintError]:
    """Check method call parameter counts using AST.

    Checks:
    - Too few arguments (MS-E020)
    - Too many arguments (MS-E021)

    Args:
        content: Plugin file content

    Returns:
        List of lint errors
    """
    from .ast import get_method_calls

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
