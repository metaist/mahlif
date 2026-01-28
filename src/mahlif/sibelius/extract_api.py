#!/usr/bin/env python3
"""Extract ManuScript API signatures from PDF manual.

Usage:
    pdftotext "ManuScript Language.pdf" - | python extract_api.py > manuscript_api.json
"""

from __future__ import annotations

import json
import re
import sys


def parse_signature(sig: str) -> dict[str, object] | None:
    """Parse a method signature into structured form.

    Examples:
        AddNote(pos,pitch,dur,[tied,[voice]]) -> {
            "name": "AddNote",
            "min_params": 3,
            "max_params": 5,
            "params": ["pos", "pitch", "dur", "tied?", "voice?"]
        }
    """
    # Match: MethodName(params)
    match = re.match(r"^([A-Z][a-zA-Z0-9_]*)\(([^)]*)\)$", sig.strip())
    if not match:
        return None

    name = match.group(1)
    params_str = match.group(2).strip()

    if not params_str:
        return {"name": name, "min_params": 0, "max_params": 0, "params": []}

    # Parse parameters, handling nested brackets for optional params
    params: list[str] = []
    min_params = 0
    in_optional = 0
    current_param = ""

    i = 0
    while i < len(params_str):
        char = params_str[i]

        if char == "[":
            in_optional += 1
            # Start of optional section - save current param if any
            if current_param.strip():
                params.append(current_param.strip())
                if in_optional == 1:
                    min_params = len(params)
                current_param = ""
        elif char == "]":
            in_optional = max(0, in_optional - 1)
            if current_param.strip():
                params.append(current_param.strip() + "?")
                current_param = ""
        elif char == ",":
            if current_param.strip():
                suffix = "?" if in_optional > 0 else ""
                params.append(current_param.strip() + suffix)
                current_param = ""
        else:
            current_param += char

        i += 1

    # Handle last param
    if current_param.strip():
        suffix = "?" if in_optional > 0 else ""
        params.append(current_param.strip() + suffix)

    # If no optional params found, all are required
    if min_params == 0:
        min_params = len([p for p in params if not p.endswith("?")])

    max_params = len(params)

    return {
        "name": name,
        "min_params": min_params,
        "max_params": max_params,
        "params": params,
    }


def extract_signatures(text: str) -> dict[str, dict[str, object]]:
    """Extract all method signatures from manual text."""
    methods: dict[str, dict[str, object]] = {}

    # Pattern for method signatures at start of line
    # Examples: AddNote(pos,pitch,dur,[tied,[voice]])
    sig_pattern = re.compile(r"^([A-Z][a-zA-Z0-9_]*\([^)]*\))\s*$", re.MULTILINE)

    for match in sig_pattern.finditer(text):
        sig = match.group(1)
        parsed = parse_signature(sig)
        if parsed:
            name = str(parsed["name"])
            max_params_val = parsed["max_params"]
            max_params = int(max_params_val) if isinstance(max_params_val, int) else 0
            # Keep the one with most params if duplicate
            if name not in methods:
                methods[name] = parsed
            else:
                existing_val = methods[name]["max_params"]
                existing_max = int(existing_val) if isinstance(existing_val, int) else 0
                if max_params > existing_max:
                    methods[name] = parsed

    return methods


def main() -> int:
    """Main entry point."""
    text = sys.stdin.read()
    methods = extract_signatures(text)

    # Output as JSON
    output = {"version": "1.0", "source": "ManuScript Language.pdf", "methods": methods}

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
