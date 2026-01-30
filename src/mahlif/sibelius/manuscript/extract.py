#!/usr/bin/env python3
"""Extract ManuScript language data from PDF manual.

Generates a comprehensive JSON file containing:
- Object types with their methods and properties
- Global constants
- Built-in functions

Usage:
    pdftotext "ManuScript Language.pdf" - | python extract.py > lang.json

The output can be used for:
- Linting (undefined variable/method detection)
- Code completion (LSP)
- Hover documentation
- Signature help

TODO: Extract parameter and return types from description text.
The PDF documents types in prose (e.g., "takes a string", "returns the Bar object").
Pattern matching or NLP could extract these for better LSP support:
- Parameter types for type checking
- Return types for chained method completion
- Property types for assignment validation
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field


class RegexMatch(str):
    """String subclass that matches against regex patterns in match/case."""

    def __eq__(self, pattern: object) -> bool:
        if isinstance(pattern, str):
            return bool(re.fullmatch(pattern, self))
        return super().__eq__(pattern)

    def __hash__(self) -> int:
        return super().__hash__()


def _is_section_header(line: str, next_lines: list[str]) -> bool:
    """Check if a line is a section header in the constants chapter.

    Section headers in the PDF follow the pattern:
    - Line contains multiple words (not a single PascalCase constant name)
    - Often followed by a Roman numeral page number
    - Contains spaces (constant names don't have spaces)

    Args:
        line: The line to check
        next_lines: The next few lines (for context)

    Returns:
        True if this looks like a section header
    """
    # Must have content
    if not line or len(line) < 3:
        return False

    # Single PascalCase word is likely a constant, not a header
    if re.match(r"^[A-Z][a-zA-Z0-9_]+$", line):
        return False

    # Contains spaces = likely a header like "Truth Values" or "Bar Number Formats"
    if " " in line:
        # But skip long descriptions (> 60 chars is probably prose)
        if len(line) > 60:
            return False
        # Check if followed by Roman numeral (page number)
        for next_line in next_lines[:3]:
            if re.match(r"^[clxvi]+$", next_line.strip()):
                return True
        # Or it's a known pattern like "X Values" or "X Types"
        if re.search(
            r"\b(Values|Types|Styles|Names|Options|Constants|Formats)\b", line
        ):
            return True

    # Chapter header - unreachable because "7 Global Constants" has a space
    # and matches "Constants" pattern above, but kept for clarity
    if line.startswith("7 Global Constants"):  # pragma: no cover
        return True

    return False


@dataclass
class MethodSignature:
    """A single method signature."""

    params: list[str] = field(default_factory=list)
    min_params: int = 0
    max_params: int = 0


@dataclass
class ObjectInfo:
    """Information about an object type."""

    name: str
    description: str = ""
    methods: dict[str, list[MethodSignature]] = field(default_factory=dict)
    properties: list[str] = field(default_factory=list)


def parse_signature(sig: str) -> tuple[str, MethodSignature] | None:
    """Parse a method signature string.

    Args:
        sig: Signature like "AddNote(pos,pitch,[tied,[voice]])"

    Returns:
        Tuple of (method_name, MethodSignature) or None if invalid
    """
    match = re.match(r"^([A-Z][a-zA-Z0-9_]*)\(([^)]*)\)$", sig.strip())
    if not match:
        return None

    name = match.group(1)
    params_str = match.group(2).strip()

    if not params_str:
        return name, MethodSignature(params=[], min_params=0, max_params=0)

    # Parse parameters, handling nested brackets for optional params
    params: list[str] = []
    min_params = 0
    in_optional = 0
    current_param = ""

    for char in params_str:
        match char:
            case "[":
                in_optional += 1
                if current_param.strip():
                    params.append(current_param.strip())
                    if in_optional == 1:
                        min_params = len(params)
                    current_param = ""
            case "]":
                in_optional = max(0, in_optional - 1)
                if current_param.strip():
                    params.append(current_param.strip() + "?")
                    current_param = ""
            case ",":
                if current_param.strip():
                    suffix = "?" if in_optional > 0 else ""
                    params.append(current_param.strip() + suffix)
                    current_param = ""
            case _:
                current_param += char

    if current_param.strip():
        suffix = "?" if in_optional > 0 else ""
        params.append(current_param.strip() + suffix)

    if min_params == 0:
        min_params = len([p for p in params if not p.endswith("?")])

    return name, MethodSignature(
        params=params, min_params=min_params, max_params=len(params)
    )


def extract_objects(lines: list[str]) -> dict[str, ObjectInfo]:
    """Extract object types with their methods and properties.

    Args:
        lines: Lines from the PDF text

    Returns:
        Dict mapping object names to ObjectInfo
    """
    objects: dict[str, ObjectInfo] = {}

    # Find object section starts: ObjectName followed by Methods within 15 lines
    object_starts: list[tuple[str, int, int]] = []
    for i, line in enumerate(lines):
        text = line.strip()
        if (
            not text
            or re.match(r"^[clxvi]+$", text)
            or text in ["l", "Methods", "Variables"]
        ):
            continue

        # Single PascalCase word (potential object name)
        if re.match(r"^[A-Z][a-z]+[A-Za-z]*$", text) and 2 < len(text) < 30:
            for j in range(i + 1, min(i + 15, len(lines))):
                if lines[j].strip() == "Methods":
                    object_starts.append((text, i, j))
                    break

    # Extract methods and properties for each object
    for idx, (obj_name, obj_line, methods_line) in enumerate(object_starts):
        end_line = (
            object_starts[idx + 1][1] if idx + 1 < len(object_starts) else len(lines)
        )

        # Get description
        desc_lines = []
        for i in range(obj_line + 1, methods_line):
            text = lines[i].strip()
            if text and text != "l" and not re.match(r"^[clxvi]+$", text):
                desc_lines.append(text)
        description = " ".join(desc_lines)

        methods: dict[str, list[MethodSignature]] = {}
        properties: list[str] = []
        in_methods = False
        in_variables = False

        for i in range(methods_line, end_line):
            text = lines[i].strip()

            if text == "Methods":
                in_methods, in_variables = True, False
                continue
            if text == "Variables":
                in_methods, in_variables = False, True
                continue

            if not text or text == "l" or re.match(r"^[clxvi]+$", text):
                continue
            if text.startswith("4 Object Reference"):
                continue

            if in_methods:
                match = re.match(r"^([A-Z][a-zA-Z0-9_]*\([^)]*\))\s*$", text)
                if match:
                    result = parse_signature(match.group(1))
                    if result:  # pragma: no branch - regex ensures valid format
                        method_name, sig = result
                        if method_name not in methods:
                            methods[method_name] = []
                        methods[method_name].append(sig)

            if in_variables:
                match = re.match(r"^([A-Z][a-zA-Z0-9_]+)$", text)
                if match and text not in [
                    "Methods",
                    "Variables",
                    "True",
                    "False",
                    "None",
                ]:
                    properties.append(text)

        # Merge or create
        if obj_name not in objects:
            objects[obj_name] = ObjectInfo(
                name=obj_name,
                description=description,
                methods=methods,
                properties=properties,
            )
        else:
            for method_name, sigs in methods.items():
                if method_name not in objects[obj_name].methods:
                    objects[obj_name].methods[method_name] = []
                objects[obj_name].methods[method_name].extend(sigs)
            objects[obj_name].properties.extend(properties)

    # Deduplicate properties
    for obj in objects.values():
        obj.properties = list(dict.fromkeys(obj.properties))

    return objects


def extract_constants(lines: list[str]) -> dict[str, int | str]:
    """Extract global constants from Chapter 7.

    Args:
        lines: Lines from the PDF text

    Returns:
        Dict mapping constant names to values (int or str)
    """
    constants: dict[str, int | str] = {}

    # Find constants section start (Truth Values after line 10000)
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "Truth Values" and i > 10000:
            start_idx = i
            break

    if start_idx is None:
        return constants

    # Find end (Index section)
    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        if lines[i].strip() == "Index":
            end_idx = i
            break

    i = start_idx
    while i < end_idx:
        text = lines[i].strip()

        # Skip noise
        if not text or re.match(r"^[clxvi]+$", text):
            i += 1
            continue

        # Skip section headers (detected by heuristic)
        next_lines = [lines[j] if j < end_idx else "" for j in range(i + 1, i + 5)]
        if _is_section_header(text, next_lines):
            i += 1
            continue

        # Skip long descriptions
        if " " in text and len(text) > 40:
            i += 1
            continue

        # Check for constant: PascalCase name(s) like "Name" or "Name or Name2"
        name_match = re.match(
            r"^([A-Z][a-zA-Z0-9_]+)(\s+or\s+[A-Z][a-zA-Z0-9_]+)*$", text
        )
        if name_match:
            names = [n.strip() for n in re.split(r"\s+or\s+", text)]

            # Look for value in next few lines
            value: int | str | None = None
            j = i + 1
            for j in range(i + 1, min(i + 5, end_idx)):
                val_line = lines[j].strip()
                match RegexMatch(val_line):
                    case "":
                        continue
                    case r"^-?\d+$":
                        value = int(val_line)
                        break
                    case r'^"[^"]*"$':
                        value = val_line.strip('"')
                        break
                    case r"^[A-Z][a-zA-Z0-9_]+":
                        # Hit another constant name
                        break
                    case _:
                        continue

            if value is not None:
                for name in names:
                    constants[name] = value
            i = j + 1 if value is not None else i + 1
        else:
            i += 1

    return constants


def get_builtin_functions() -> dict[str, dict[str, object]]:
    """Return built-in global functions.

    These are documented in various places in the manual but not in a
    consistent format that's easy to parse. This list covers the most
    commonly used functions.

    Returns:
        Dict of function info with params and return types
    """
    # NOTE: These could potentially be extracted from the PDF's "Global Functions"
    # or "Built-in Functions" sections if we find a reliable pattern
    return {
        "CreateSparseArray": {"returns": "SparseArray", "params": []},
        "CreateArray": {"returns": "Array", "params": []},
        "CreateDictionary": {"returns": "Dictionary", "params": []},
        "CreateHash": {"returns": "Hash", "params": []},
        "Trace": {"returns": "void", "params": ["message"]},
        "StopPlugin": {"returns": "void", "params": []},
        "TypeOf": {"returns": "string", "params": ["object"]},
        "IsObject": {"returns": "boolean", "params": ["value"]},
        "Chr": {"returns": "string", "params": ["code"]},
        "Asc": {"returns": "int", "params": ["char"]},
        "CharAt": {"returns": "string", "params": ["string", "index"]},
        "Length": {"returns": "int", "params": ["string"]},
        "Substring": {"returns": "string", "params": ["string", "start", "length?"]},
        "JoinStrings": {"returns": "string", "params": ["array", "separator"]},
        "SplitString": {"returns": "array", "params": ["string", "separator"]},
        "Round": {"returns": "int", "params": ["number"]},
        "RoundUp": {"returns": "int", "params": ["number"]},
        "RoundDown": {"returns": "int", "params": ["number"]},
        "Abs": {"returns": "int", "params": ["number"]},
        "Min": {"returns": "number", "params": ["a", "b"]},
        "Max": {"returns": "number", "params": ["a", "b"]},
        "RandomNumber": {"returns": "int", "params": []},
        "RandomSeed": {"returns": "void", "params": ["seed"]},
    }


def main() -> int:
    """Extract language data from PDF text on stdin, output JSON."""
    text = sys.stdin.read()
    lines = text.split("\n")

    objects = extract_objects(lines)
    constants = extract_constants(lines)
    builtin_functions = get_builtin_functions()

    # Convert to JSON-serializable format
    objects_json: dict[str, object] = {}
    for name, obj in objects.items():
        methods_json: dict[str, object] = {}
        for method_name, sigs in obj.methods.items():
            methods_json[method_name] = {
                "signatures": [
                    {
                        "params": sig.params,
                        "min_params": sig.min_params,
                        "max_params": sig.max_params,
                    }
                    for sig in sigs
                ]
            }
        objects_json[name] = {
            "description": obj.description,
            "methods": methods_json,
            "properties": obj.properties,
        }

    output = {
        "version": "1.0",
        "source": "ManuScript Language.pdf",
        "objects": objects_json,
        "constants": constants,
        "builtin_functions": builtin_functions,
    }

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
