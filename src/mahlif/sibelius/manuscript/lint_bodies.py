"""Method body extraction and checking."""

from __future__ import annotations

import re

from .errors import LintError


def extract_method_bodies(content: str) -> list[tuple[str, str, int, int]]:
    """Extract method bodies from plugin content.

    ManuScript method bodies are embedded as strings:
        MethodName "(params) { body }"

    Args:
        content: Plugin file content

    Returns:
        List of (method_name, body_content, start_line, start_col) tuples
    """
    methods: list[tuple[str, str, int, int]] = []
    lines = content.split("\n")

    # Pattern to match method definitions: Name "(params) { body }"
    # We need to find the opening " and then match the closing "
    method_start_pattern = re.compile(r'^\s*(\w+)\s+"')

    i = 0
    while i < len(lines):
        line = lines[i]
        match = method_start_pattern.match(line)
        if match:
            method_name = match.group(1)
            # Find the position of the opening quote
            quote_pos = line.index('"', match.start(1))
            start_line = i + 1
            start_col = quote_pos + 2  # After the opening quote

            # Now we need to find the matching closing quote
            # The body might span multiple lines
            body_start = quote_pos + 1
            body_lines = [line[body_start:]]
            j = i

            # Track whether we're in a nested string
            in_nested_string = False
            nested_quote_char = None

            # Find the closing quote
            found_end = False
            while j < len(lines) and not found_end:
                check_line = lines[j] if j > i else line[body_start:]
                k = 0 if j > i else 0

                while k < len(check_line):
                    char = check_line[k]

                    # Handle escape sequences
                    if char == "\\" and k + 1 < len(check_line):
                        k += 2
                        continue

                    # Track nested strings (single quotes inside double-quoted method body)
                    if not in_nested_string and char == "'":
                        in_nested_string = True
                        nested_quote_char = "'"
                    elif in_nested_string and char == nested_quote_char:
                        in_nested_string = False
                        nested_quote_char = None
                    elif not in_nested_string and char == '"':
                        # Found the closing quote
                        if j == i:
                            body_content = line[body_start : body_start + k]
                        else:
                            body_lines[-1] = check_line[:k]
                            body_content = "\n".join(body_lines)
                        methods.append(
                            (method_name, body_content, start_line, start_col)
                        )
                        found_end = True
                        break

                    k += 1

                if not found_end:
                    j += 1
                    if j < len(lines):
                        body_lines.append(lines[j])

            i = j + 1
        else:
            i += 1

    return methods


def extract_plugin_variables(content: str) -> set[str]:
    """Extract plugin-level variable names.

    Plugin variables are defined as: VarName "value"
    These are available to all methods in the plugin.

    Args:
        content: Plugin file content

    Returns:
        Set of variable names defined at plugin level
    """
    variables: set[str] = set()
    lines = content.split("\n")

    # Pattern: identifier followed by quoted string (variable definition)
    # But NOT Initialize, Run, or method-like names with () in the string
    var_pattern = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s+"[^(]')

    for line in lines:
        match = var_pattern.match(line)
        if match:
            name = match.group(1)
            # Exclude known method names
            if name not in {"Initialize", "Run"}:
                variables.add(name)

    return variables


def lint_method_bodies(content: str) -> list[LintError]:
    """Check method body content for syntax errors.

    Uses the manuscript checker to perform deep syntax checking
    of method body content.

    Args:
        content: Plugin file content

    Returns:
        List of lint errors
    """
    from .checker import check_method_body

    errors: list[LintError] = []
    methods = extract_method_bodies(content)
    plugin_vars = extract_plugin_variables(content)

    for method_name, body, start_line, start_col in methods:
        # Extract parameters from body (format: "(params) { code }")
        params: list[str] = []
        if body.startswith("("):
            paren_end = body.find(")")
            if paren_end > 0:  # pragma: no branch - parser ensures valid structure
                params_str = body[1:paren_end]
                if params_str.strip():
                    params = [p.strip() for p in params_str.split(",")]

                # Find the body content after the parameters
                brace_start = body.find("{", paren_end)
                if (
                    brace_start >= 0
                ):  # pragma: no branch - parser ensures valid structure
                    brace_end = body.rfind("}")
                    if brace_end > brace_start:  # pragma: no branch
                        actual_body = body[brace_start + 1 : brace_end]
                        # Calculate the actual start position
                        body_line = start_line
                        body_col = start_col + brace_start + 1

                        # Check the body
                        check_errors = check_method_body(
                            actual_body,
                            method_name,
                            body_line,
                            body_col,
                            params,
                            plugin_vars,
                        )

                        # Convert CheckErrors to LintErrors
                        for err in check_errors:
                            errors.append(
                                LintError(err.line, err.col, err.code, err.message)
                            )

    return errors
