"""Error types and codes for ManuScript linting.

Error Code Ranges:
- MS-E0xx: Plugin structure errors
- MS-E02x: Method call validation
- MS-E03x: Tokenization errors
- MS-E04x: Parse/syntax errors
- MS-W0xx: Style warnings
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LintError:
    """An error found during linting/checking."""

    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.line}:{self.col} [{self.code}] {self.message}"


# Backwards compatibility alias
CheckError = LintError


# Error code constants for documentation and consistency
# Plugin structure (MS-E00x, MS-E01x)
E001_UNMATCHED_CLOSE = "MS-E001"  # Unmatched closing brace
E002_MISSING_BODY = "MS-E002"  # Missing method body
E003_UNCLOSED = "MS-E003"  # Unclosed brace
E010_NO_OPEN_BRACE = "MS-E010"  # Plugin must start with '{'
E011_NO_CLOSE_BRACE = "MS-E011"  # Plugin must end with '}'

# Method call validation (MS-E02x)
E020_UNKNOWN_METHOD = "MS-E020"  # Unknown API method
E021_WRONG_ARGS = "MS-E021"  # Wrong argument count

# Tokenization errors (MS-E03x)
E030_UNTERMINATED_STRING = "MS-E030"  # Unterminated string
E031_UNEXPECTED_CHAR = "MS-E031"  # Unexpected character

# Parse/syntax errors (MS-E04x)
E040_EXPECTED_TOKEN = "MS-E040"  # Expected specific token
E041_FOR_EACH_SYNTAX = "MS-E041"  # Invalid for each syntax
E042_SWITCH_SYNTAX = "MS-E042"  # Expected case/default in switch
E043_MISSING_BRACE = "MS-E043"  # Missing required braces
E044_MISSING_SEMICOLON = "MS-E044"  # Missing semicolon
E045_EXPECTED_EXPR = "MS-E045"  # Expected expression
E046_INCOMPLETE_OP = "MS-E046"  # Expected expression after operator
E047_EXPECTED_PROPERTY = "MS-E047"  # Expected property name after dot
E048_UNEXPECTED_TOKEN = "MS-E048"  # Unexpected token

# Style warnings (MS-W0xx)
W001_DEPRECATED = "MS-W001"  # Deprecated API
W002_TRAILING_WS = "MS-W002"  # Trailing whitespace
W003_INDENT = "MS-W003"  # Inconsistent indent
W010_NO_INIT = "MS-W010"  # Missing Initialize method
W011_NO_MENU = "MS-W011"  # Initialize should call AddToPluginsMenu

# Semantic warnings (MS-W02x)
W020_UNDEFINED_VAR = "MS-W020"  # Possibly undefined variable

# Runtime warnings (MS-W02x)
W021_FOR_LOOP_BOUNDS = "MS-W021"  # For loop end could be negative
