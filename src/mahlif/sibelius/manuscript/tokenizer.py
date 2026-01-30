"""Tokenizer for ManuScript method body content.

ManuScript method bodies are embedded as strings in plugin files:
    MethodName "(params) { body }"

This module tokenizes the content inside these strings for syntax checking.
"""

from __future__ import annotations

from typing import Iterator

from .errors import CheckError
from .tokens import KEYWORDS
from .tokens import Token
from .tokens import TokenType


# Re-export for backwards compatibility
__all__ = ["Token", "TokenType", "MethodBodyTokenizer", "KEYWORDS"]


class MethodBodyTokenizer:
    """Tokenize ManuScript method body content."""

    def __init__(self, source: str, start_line: int = 1, start_col: int = 1) -> None:
        """Initialize tokenizer.

        Args:
            source: Method body source code
            start_line: Line number where this method body starts in the file
            start_col: Column where this method body starts
        """
        self.source = source
        self.pos = 0
        self.line = start_line
        self.col = start_col
        self.errors: list[CheckError] = []

    def tokenize(self) -> Iterator[Token]:
        """Generate tokens from source."""
        while self.pos < len(self.source):
            start_line = self.line
            start_col = self.col

            char = self.source[self.pos]

            # Whitespace (not newline)
            if char in " \t\r":
                self._advance()
                continue

            # Newline - _advance() handles line/col tracking
            if char == "\n":
                self._advance()
                continue

            # Comment
            if char == "/" and self._peek(1) == "/":
                comment = self._read_until("\n")
                yield Token(TokenType.COMMENT, comment, start_line, start_col)
                continue

            # String (single or double quote)
            if char in "'\"":
                string, error = self._read_string(char)
                if error:
                    self.errors.append(
                        CheckError(
                            start_line, start_col, "MS-E030", "Unterminated string"
                        )
                    )
                    yield Token(TokenType.ERROR, string, start_line, start_col)
                else:
                    yield Token(TokenType.STRING, string, start_line, start_col)
                continue

            # Number
            if char.isdigit():
                number = self._read_number()
                yield Token(TokenType.NUMBER, number, start_line, start_col)
                continue

            # Negative number (only if followed by digit)
            if char == "-" and self._peek(1).isdigit():
                number = self._read_number()
                yield Token(TokenType.NUMBER, number, start_line, start_col)
                continue

            # Identifier or keyword
            if char.isalpha() or char == "_":
                ident = self._read_identifier()
                token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
                yield Token(token_type, ident, start_line, start_col)
                continue

            # Two-character operators
            two_char = self.source[self.pos : self.pos + 2]
            if two_char == "<=":
                self._advance(2)
                yield Token(TokenType.LTE, "<=", start_line, start_col)
                continue
            if two_char == ">=":
                self._advance(2)
                yield Token(TokenType.GTE, ">=", start_line, start_col)
                continue
            if two_char == "!=":
                self._advance(2)
                yield Token(TokenType.NEQ, "!=", start_line, start_col)
                continue

            # Single-character tokens
            single_char_tokens = {
                "=": TokenType.ASSIGN,
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "&": TokenType.AMPERSAND,
                "<": TokenType.LT,
                ">": TokenType.GT,
                ".": TokenType.DOT,
                ":": TokenType.COLON,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                ",": TokenType.COMMA,
                ";": TokenType.SEMICOLON,
            }

            if char in single_char_tokens:
                self._advance()
                yield Token(single_char_tokens[char], char, start_line, start_col)
                continue

            # Unknown character - report error but continue
            self.errors.append(
                CheckError(
                    start_line, start_col, "MS-E031", f"Unexpected character '{char}'"
                )
            )
            self._advance()

        yield Token(TokenType.EOF, "", self.line, self.col)

    def _advance(self, n: int = 1) -> None:
        """Advance position by n characters."""
        for _ in range(n):
            if self.pos < len(self.source):
                if self.source[self.pos] == "\n":
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.pos += 1

    def _peek(self, offset: int = 0) -> str:
        """Peek at character at current position + offset."""
        pos = self.pos + offset
        if pos < len(self.source):
            return self.source[pos]
        return ""  # pragma: no cover - defensive for peek past end

    def _read_until(self, char: str) -> str:
        """Read until character (exclusive)."""
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != char:
            self._advance()
        return self.source[start : self.pos]

    def _read_string(self, quote: str) -> tuple[str, bool]:
        """Read a string literal including quotes.

        Returns:
            Tuple of (string content, is_error)
        """
        start = self.pos
        self._advance()  # Opening quote
        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char == "\\":
                self._advance(2)  # Skip escape sequence
            elif char == quote:
                self._advance()  # Closing quote
                return self.source[start : self.pos], False
            elif char == "\n":
                # Unterminated string at end of line
                return self.source[start : self.pos], True
            else:
                self._advance()
        # Unterminated string at end of input
        return self.source[start : self.pos], True

    def _read_number(self) -> str:
        """Read a number literal."""
        start = self.pos
        if self.source[self.pos] == "-":
            self._advance()
        while self.pos < len(self.source) and (
            self.source[self.pos].isdigit() or self.source[self.pos] == "."
        ):
            self._advance()
        return self.source[start : self.pos]

    def _read_identifier(self) -> str:
        """Read an identifier."""
        start = self.pos
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] == "_"
        ):
            self._advance()
        return self.source[start : self.pos]
