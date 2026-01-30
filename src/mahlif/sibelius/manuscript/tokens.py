"""Unified token types for ManuScript parsing.

This module defines the Token and TokenType used by both the plugin-level
parser (ast.py) and the method body checker (checker.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from enum import auto


class TokenType(Enum):
    """Token types for ManuScript."""

    # Literals
    STRING = auto()
    NUMBER = auto()
    IDENTIFIER = auto()

    # Keywords
    IF = auto()
    ELSE = auto()
    FOR = auto()
    EACH = auto()
    IN = auto()
    TO = auto()
    WHILE = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    RETURN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    # Operators
    PLUS = auto()  # +
    MINUS = auto()  # -
    STAR = auto()  # *
    SLASH = auto()  # /
    PERCENT = auto()  # %
    AMPERSAND = auto()  # & (string concat)
    ASSIGN = auto()  # = (also equality in ManuScript)
    LT = auto()  # <
    GT = auto()  # >
    LTE = auto()  # <=
    GTE = auto()  # >=
    NEQ = auto()  # != or <>

    # Punctuation
    DOT = auto()  # .
    COLON = auto()  # :
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    COMMA = auto()  # ,
    SEMICOLON = auto()  # ;

    # Special
    COMMENT = auto()
    EOF = auto()
    ERROR = auto()  # For tokenization errors


@dataclass
class Token:
    """A token in ManuScript source."""

    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"


KEYWORDS: dict[str, TokenType] = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "each": TokenType.EACH,
    "in": TokenType.IN,
    "to": TokenType.TO,
    "while": TokenType.WHILE,
    "switch": TokenType.SWITCH,
    "case": TokenType.CASE,
    "default": TokenType.DEFAULT,
    "return": TokenType.RETURN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "True": TokenType.TRUE,
    "true": TokenType.TRUE,
    "False": TokenType.FALSE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}
