#!/usr/bin/env python3
"""ManuScript AST for parsing Sibelius plugin files.

This provides a proper tokenizer and AST for better linting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from typing import Iterator

from .tokens import KEYWORDS
from .tokens import Token
from .tokens import TokenType

__all__ = [
    "KEYWORDS",
    "Token",
    "TokenType",
    "Tokenizer",
    "Parser",
    "Plugin",
    "MethodDef",
    "VarDef",
    "parse_plugin",
    "get_method_calls",
]


class Tokenizer:
    """Tokenize ManuScript source code."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def tokenize(self) -> Iterator[Token]:
        """Generate tokens from source."""
        while self.pos < len(self.source):
            # Track position for token
            start_line = self.line
            start_col = self.col

            char = self.source[self.pos]

            # Whitespace (not newline)
            if char in " \t\r":
                self._advance()
                continue

            # Newline
            if char == "\n":
                self._advance()
                self.line += 1
                self.col = 1
                continue

            # Comment
            if char == "/" and self._peek(1) == "/":
                comment = self._read_until("\n")
                yield Token(TokenType.COMMENT, comment, start_line, start_col)
                continue

            # String (single or double quote)
            if char in "'\"":
                string = self._read_string(char)
                yield Token(TokenType.STRING, string, start_line, start_col)
                continue

            # Number
            if char.isdigit() or (char == "-" and self._peek(1).isdigit()):
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

            # Unknown character - skip
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
        return ""

    def _read_until(self, char: str) -> str:
        """Read until character (exclusive)."""
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != char:
            self._advance()
        return self.source[start : self.pos]

    def _read_string(self, quote: str) -> str:
        """Read a string literal including quotes."""
        start = self.pos
        self._advance()  # Opening quote
        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char == "\\":
                self._advance(2)  # Skip escape sequence
            elif char == quote:
                self._advance()  # Closing quote
                break
            else:
                self._advance()
        return self.source[start : self.pos]

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


# AST Node types
@dataclass
class ASTNode:
    """Base class for AST nodes."""

    line: int = 0
    col: int = 0


@dataclass
class Plugin(ASTNode):
    """Root node for a plugin file."""

    members: list[PluginMember] = field(default_factory=list)


@dataclass
class PluginMember(ASTNode):
    """A member of the plugin (method or variable)."""

    pass


@dataclass
class MethodDef(PluginMember):
    """A method definition."""

    name: str = ""
    params: list[str] = field(default_factory=list)
    body: list[Statement] = field(default_factory=list)


@dataclass
class VarDef(PluginMember):
    """A variable definition at plugin level."""

    name: str = ""
    value: str = ""


@dataclass
class Statement(ASTNode):
    """Base class for statements."""

    pass


@dataclass
class Assignment(Statement):
    """Variable assignment."""

    target: str = ""
    value: Expression | None = None


@dataclass
class MethodCall(Statement):
    """A method call (can also be an expression)."""

    object: str | None = None  # None for global functions
    method: str = ""
    args: list[Expression] = field(default_factory=list)


@dataclass
class IfStatement(Statement):
    """If statement."""

    condition: Expression | None = None
    then_body: list[Statement] = field(default_factory=list)
    else_body: list[Statement] = field(default_factory=list)


@dataclass
class ForLoop(Statement):
    """For loop (for i = a to b or for each x in y)."""

    var: str = ""
    is_foreach: bool = False
    start: Expression | None = None  # for i = start to end
    end: Expression | None = None
    collection: Expression | None = None  # for each x in collection
    body: list[Statement] = field(default_factory=list)


@dataclass
class WhileLoop(Statement):
    """While loop."""

    condition: Expression | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass
class ReturnStatement(Statement):
    """Return statement."""

    value: Expression | None = None


@dataclass
class Expression(ASTNode):
    """Base class for expressions."""

    pass


@dataclass
class Literal(Expression):
    """A literal value (string, number, bool, null)."""

    value: str = ""
    literal_type: str = ""  # "string", "number", "bool", "null"


@dataclass
class Identifier(Expression):
    """A variable reference."""

    name: str = ""


@dataclass
class BinaryOp(Expression):
    """Binary operation."""

    left: Expression | None = None
    op: str = ""
    right: Expression | None = None


@dataclass
class CallExpr(Expression):
    """Method/function call as expression."""

    object: Expression | None = None
    method: str = ""
    args: list[Expression] = field(default_factory=list)


@dataclass
class IndexExpr(Expression):
    """Array/object index access."""

    object: Expression | None = None
    index: Expression | None = None


class Parser:
    """Parse ManuScript tokens into AST."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Plugin:
        """Parse a complete plugin file."""
        plugin = Plugin()

        # Expect opening brace
        self._expect(TokenType.LBRACE)

        # Parse members until closing brace
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            member = self._parse_plugin_member()
            if member:
                plugin.members.append(member)

        self._expect(TokenType.RBRACE)
        return plugin

    def _parse_plugin_member(self) -> PluginMember | None:
        """Parse a plugin member (method or variable def)."""
        if not self._check(TokenType.IDENTIFIER):
            self._advance()
            return None

        name_token = self._advance()
        name = name_token.value

        # Method or variable: Name "..."
        if self._check(TokenType.STRING):
            string_token = self._advance()
            content = string_token.value[1:-1]  # Strip quotes

            # Check if it looks like a method: "(params) { body }"
            if content.startswith("("):
                method = MethodDef(name=name, line=name_token.line, col=name_token.col)
                # Parse params and body from string content
                # This is simplified - real parsing would tokenize the string
                method.params = self._extract_params(content)
                return method
            else:
                # Variable definition
                return VarDef(
                    name=name,
                    value=content,
                    line=name_token.line,
                    col=name_token.col,
                )

        return None

    def _extract_params(self, content: str) -> list[str]:
        """Extract parameter names from method signature string."""
        # Find params between ( and )
        match = re.match(r"\(([^)]*)\)", content)
        if match:
            params_str = match.group(1).strip()
            if params_str:
                return [p.strip() for p in params_str.split(",")]
        return []

    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type."""
        if self.pos >= len(self.tokens):
            return token_type == TokenType.EOF
        return self.tokens[self.pos].type == token_type

    def _advance(self) -> Token:
        """Advance and return current token."""
        token = (
            self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]
        )
        self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        """Expect and consume a token of given type."""
        if not self._check(token_type):
            current = (
                self.tokens[self.pos]
                if self.pos < len(self.tokens)
                else self.tokens[-1]
            )
            raise SyntaxError(
                f"Expected {token_type.name}, got {current.type.name} "
                f"at line {current.line}:{current.col}"
            )
        return self._advance()


def parse_plugin(source: str) -> Plugin:
    """Parse ManuScript source into AST."""
    # Strip BOM if present
    if source.startswith("\ufeff"):
        source = source[1:]

    tokenizer = Tokenizer(source)
    tokens = list(tokenizer.tokenize())
    parser = Parser(tokens)
    return parser.parse()


def get_method_calls(source: str) -> list[tuple[int, int, str | None, str, int]]:
    """Extract method calls from source.

    Returns list of (line, col, object, method, arg_count) tuples.
    """
    calls: list[tuple[int, int, str | None, str, int]] = []

    tokenizer = Tokenizer(source)
    tokens = list(tokenizer.tokenize())

    i = 0
    while i < len(tokens):
        # Look for pattern: IDENTIFIER DOT IDENTIFIER LPAREN or IDENTIFIER LPAREN
        if tokens[i].type == TokenType.IDENTIFIER:
            obj: str | None = None
            method: str
            method_line: int
            method_col: int

            if i + 2 < len(tokens) and tokens[i + 1].type == TokenType.DOT:
                # obj.method(...)
                if tokens[i + 2].type == TokenType.IDENTIFIER:
                    obj = tokens[i].value
                    method = tokens[i + 2].value
                    method_line = tokens[i + 2].line
                    method_col = tokens[i + 2].col
                    i += 3
                else:
                    i += 1
                    continue
            else:
                # method(...)
                method = tokens[i].value
                method_line = tokens[i].line
                method_col = tokens[i].col
                i += 1

            # Check for LPAREN
            if i < len(tokens) and tokens[i].type == TokenType.LPAREN:
                i += 1
                # Count arguments
                arg_count = 0
                depth = 1
                has_content = False

                while i < len(tokens) and depth > 0:
                    if tokens[i].type == TokenType.LPAREN:
                        depth += 1
                        has_content = True
                    elif tokens[i].type == TokenType.RPAREN:
                        depth -= 1
                    elif tokens[i].type == TokenType.COMMA and depth == 1:
                        arg_count += 1
                    elif tokens[i].type != TokenType.COMMENT:
                        has_content = True
                    i += 1

                if has_content:
                    arg_count += 1

                calls.append((method_line, method_col, obj, method, arg_count))
        else:
            i += 1

    return calls
