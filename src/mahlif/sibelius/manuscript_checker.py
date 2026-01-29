"""Comprehensive syntax and semantic checker for ManuScript.

This module parses method body content (which is embedded in strings) and
performs thorough checking including:
- Syntax errors (incomplete expressions, missing semicolons, etc.)
- Control flow validation (if/while/for/switch structure)
- Undefined variable detection
- Method call validation
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from enum import auto
from typing import Iterator


class TokenType(Enum):
    """Token types for ManuScript method bodies."""

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
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Operators
    ASSIGN = auto()  # =
    PLUS = auto()  # +
    MINUS = auto()  # -
    STAR = auto()  # *
    SLASH = auto()  # /
    PERCENT = auto()  # %
    AMPERSAND = auto()  # & (string concat)
    LT = auto()  # <
    GT = auto()  # >
    LTE = auto()  # <=
    GTE = auto()  # >=
    NEQ = auto()  # !=
    DOT = auto()  # .
    COLON = auto()  # :

    # Delimiters
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


KEYWORDS = {
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
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "True": TokenType.TRUE,
    "False": TokenType.FALSE,
}


@dataclass
class CheckError:
    """An error found during checking."""

    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.line}:{self.col} [{self.code}] {self.message}"


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
        return ""

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


class MethodBodyChecker:
    """Check ManuScript method body for errors."""

    def __init__(
        self,
        tokens: list[Token],
        method_name: str = "",
        defined_vars: set[str] | None = None,
    ) -> None:
        """Initialize checker.

        Args:
            tokens: List of tokens from tokenizer
            method_name: Name of the method being checked
            defined_vars: Set of pre-defined variables (parameters, globals)
        """
        self.tokens = tokens
        self.method_name = method_name
        self.pos = 0
        self.errors: list[CheckError] = []
        self.defined_vars: set[str] = defined_vars or set()
        self.local_vars: set[str] = set()

    def check(self) -> list[CheckError]:
        """Run all checks and return errors."""
        self._skip_comments()

        # Check for completely empty body
        if self._check(TokenType.EOF):
            return self.errors

        # Parse statements
        while not self._check(TokenType.EOF):
            self._parse_statement()
            self._skip_comments()

        return self.errors

    def _current(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _check(self, *types: TokenType) -> bool:
        """Check if current token is one of the given types."""
        return self._current().type in types

    def _advance(self) -> Token:
        """Advance and return current token."""
        token = self._current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _skip_comments(self) -> None:
        """Skip over comment tokens."""
        while self._check(TokenType.COMMENT):
            self._advance()

    def _expect(self, token_type: TokenType, message: str) -> Token | None:
        """Expect a specific token type, report error if not found."""
        self._skip_comments()
        if not self._check(token_type):
            token = self._current()
            self.errors.append(CheckError(token.line, token.col, "MS-E040", message))
            return None
        return self._advance()

    def _parse_statement(self) -> None:
        """Parse a single statement."""
        self._skip_comments()

        # Control flow statements
        if self._check(TokenType.IF):
            self._parse_if()
        elif self._check(TokenType.WHILE):
            self._parse_while()
        elif self._check(TokenType.FOR):
            self._parse_for()
        elif self._check(TokenType.SWITCH):
            self._parse_switch()
        elif self._check(TokenType.RETURN):
            self._parse_return()
        elif self._check(TokenType.LBRACE):
            self._parse_block()
        elif self._check(TokenType.RBRACE):
            # Unexpected closing brace - let caller handle
            return
        elif self._check(TokenType.SEMICOLON):
            # Empty statement
            self._advance()
        elif self._check(TokenType.EOF):
            return
        else:
            # Expression statement (assignment or call)
            self._parse_expression_statement()

    def _parse_if(self) -> None:
        """Parse if statement."""
        self._advance()  # consume 'if'

        # Expect (
        if not self._expect(TokenType.LPAREN, "Expected '(' after 'if'"):
            self._recover_to_brace()
            return

        # Parse condition
        self._parse_expression()

        # Expect )
        if not self._expect(TokenType.RPAREN, "Expected ')' after if condition"):
            self._recover_to_brace()
            return

        # Expect { block }
        if not self._parse_required_block("if"):
            return

        # Check for else
        self._skip_comments()
        if self._check(TokenType.ELSE):
            self._advance()
            self._skip_comments()
            if self._check(TokenType.IF):
                # else if
                self._parse_if()
            else:
                # else block
                self._parse_required_block("else")

    def _parse_while(self) -> None:
        """Parse while statement."""
        self._advance()  # consume 'while'

        if not self._expect(TokenType.LPAREN, "Expected '(' after 'while'"):
            self._recover_to_brace()
            return

        self._parse_expression()

        if not self._expect(TokenType.RPAREN, "Expected ')' after while condition"):
            self._recover_to_brace()
            return

        self._parse_required_block("while")

    def _parse_for(self) -> None:
        """Parse for/for each statement."""
        self._advance()  # consume 'for'
        self._skip_comments()

        if self._check(TokenType.EACH):
            self._parse_for_each()
        else:
            self._parse_for_to()

    def _parse_for_each(self) -> None:
        """Parse 'for each [Type] var in expr { }'."""
        self._advance()  # consume 'each'
        self._skip_comments()

        # Optional type
        if self._check(TokenType.IDENTIFIER):
            first_ident = self._advance()
            self._skip_comments()

            if self._check(TokenType.IDENTIFIER):
                # Type followed by var
                var_token = self._advance()
                self.local_vars.add(var_token.value)
            elif self._check(TokenType.IN):
                # Just var, no type
                self.local_vars.add(first_ident.value)
            else:
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-E041",
                        "Expected 'in' in for each statement",
                    )
                )
                self._recover_to_brace()
                return
        else:
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-E041",
                    "Expected variable name in for each statement",
                )
            )
            self._recover_to_brace()
            return

        # Expect 'in'
        if not self._expect(TokenType.IN, "Expected 'in' in for each statement"):
            self._recover_to_brace()
            return

        # Parse collection expression
        self._parse_expression()

        self._parse_required_block("for each")

    def _parse_for_to(self) -> None:
        """Parse 'for var = start to end { }'."""
        # Expect variable
        if not self._check(TokenType.IDENTIFIER):
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-E041",
                    "Expected variable name after 'for'",
                )
            )
            self._recover_to_brace()
            return

        var_token = self._advance()
        self.local_vars.add(var_token.value)

        # Expect =
        if not self._expect(TokenType.ASSIGN, "Expected '=' in for statement"):
            self._recover_to_brace()
            return

        # Parse start expression
        self._parse_expression()

        # Expect 'to'
        if not self._expect(TokenType.TO, "Expected 'to' in for statement"):
            self._recover_to_brace()
            return

        # Parse end expression
        self._parse_expression()

        self._parse_required_block("for")

    def _parse_switch(self) -> None:
        """Parse switch statement."""
        self._advance()  # consume 'switch'

        if not self._expect(TokenType.LPAREN, "Expected '(' after 'switch'"):
            self._recover_to_brace()
            return

        self._parse_expression()

        if not self._expect(TokenType.RPAREN, "Expected ')' after switch expression"):
            self._recover_to_brace()
            return

        if not self._expect(TokenType.LBRACE, "Expected '{' for switch body"):
            return

        # Parse case/default statements
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            self._skip_comments()
            if self._check(TokenType.CASE):
                self._parse_case()
            elif self._check(TokenType.DEFAULT):
                self._parse_default()
            elif self._check(TokenType.RBRACE):
                break
            else:
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-E042",
                        "Expected 'case' or 'default' in switch statement",
                    )
                )
                self._advance()

        self._expect(
            TokenType.RBRACE,  # pyrefly: ignore[unbound-name]
            "Expected '}' to close switch",
        )

    def _parse_case(self) -> None:
        """Parse case clause."""
        self._advance()  # consume 'case'

        if not self._expect(TokenType.LPAREN, "Expected '(' after 'case'"):
            self._recover_to_brace()
            return

        self._parse_expression()

        if not self._expect(TokenType.RPAREN, "Expected ')' after case expression"):
            self._recover_to_brace()
            return

        self._parse_required_block("case")

    def _parse_default(self) -> None:
        """Parse default clause."""
        self._advance()  # consume 'default'
        self._parse_required_block("default")

    def _parse_return(self) -> None:
        """Parse return statement."""
        self._advance()  # consume 'return'
        self._skip_comments()

        # Optional return value
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            self._parse_expression()

        self._expect(TokenType.SEMICOLON, "Expected ';' after return statement")

    def _parse_block(self) -> None:
        """Parse a block { statements }."""
        self._advance()  # consume '{'

        while not self._check(TokenType.RBRACE, TokenType.EOF):
            self._parse_statement()
            self._skip_comments()

        self._expect(TokenType.RBRACE, "Expected '}' to close block")

    def _parse_required_block(self, context: str) -> bool:
        """Parse a required block, reporting error if missing."""
        self._skip_comments()
        if not self._check(TokenType.LBRACE):
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-E043",
                    f"Expected '{{' after {context}",
                )
            )
            return False
        self._parse_block()
        return True

    def _parse_expression_statement(self) -> None:
        """Parse expression statement (assignment or function call)."""
        self._parse_expression()
        self._skip_comments()

        # Expect semicolon
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            # Check if this looks like a missing semicolon
            if self._check(
                TokenType.IDENTIFIER,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.FOR,
                TokenType.RETURN,
            ):
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-E044",
                        "Expected ';' after statement",
                    )
                )
            else:
                # Try to continue parsing
                self._advance()
        elif self._check(TokenType.SEMICOLON):
            self._advance()

    def _parse_expression(self) -> None:
        """Parse an expression."""
        self._skip_comments()

        # Handle empty expression
        if self._check(
            TokenType.SEMICOLON,
            TokenType.RPAREN,
            TokenType.RBRACKET,
            TokenType.COMMA,
            TokenType.RBRACE,
            TokenType.EOF,
        ):
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-E045",
                    "Expected expression",
                )
            )
            return

        self._parse_assignment_or_expr()

    def _parse_assignment_or_expr(self) -> None:
        """Parse assignment or simple expression."""
        # Parse left side
        self._parse_or_expr()
        self._skip_comments()

        # Check for assignment
        if self._check(TokenType.ASSIGN):
            self._advance()
            self._skip_comments()

            # Check for empty right side
            if self._check(TokenType.SEMICOLON, TokenType.RPAREN, TokenType.EOF):
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-E045",
                        "Expected expression after '='",
                    )
                )
                return

            self._parse_assignment_or_expr()

    def _parse_or_expr(self) -> None:
        """Parse OR expression."""
        self._parse_and_expr()
        while self._check(TokenType.OR):
            self._advance()
            self._parse_and_expr()

    def _parse_and_expr(self) -> None:
        """Parse AND expression."""
        self._parse_comparison()
        while self._check(TokenType.AND):
            self._advance()
            self._parse_comparison()

    def _parse_comparison(self) -> None:
        """Parse comparison expression."""
        self._parse_additive()
        while self._check(
            TokenType.ASSIGN,
            TokenType.NEQ,
            TokenType.LT,
            TokenType.GT,
            TokenType.LTE,
            TokenType.GTE,
        ):
            self._advance()
            self._parse_additive()

    def _parse_additive(self) -> None:
        """Parse additive expression (+, -, &)."""
        self._parse_multiplicative()
        while self._check(TokenType.PLUS, TokenType.MINUS, TokenType.AMPERSAND):
            self._advance()
            self._skip_comments()
            if self._check(TokenType.SEMICOLON, TokenType.RPAREN, TokenType.EOF):
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-E046",
                        "Expected expression after operator",
                    )
                )
                return
            self._parse_multiplicative()

    def _parse_multiplicative(self) -> None:
        """Parse multiplicative expression (*, /, %)."""
        self._parse_unary()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            self._advance()
            self._skip_comments()
            if self._check(TokenType.SEMICOLON, TokenType.RPAREN, TokenType.EOF):
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-E046",
                        "Expected expression after operator",
                    )
                )
                return
            self._parse_unary()

    def _parse_unary(self) -> None:
        """Parse unary expression (not, -)."""
        if self._check(TokenType.NOT, TokenType.MINUS):
            self._advance()
            self._parse_unary()
        else:
            self._parse_postfix()

    def _parse_postfix(self) -> None:
        """Parse postfix expression (calls, property access, indexing)."""
        self._parse_primary()

        while True:
            self._skip_comments()
            if self._check(TokenType.DOT):
                self._advance()
                self._skip_comments()
                if self._check(TokenType.IDENTIFIER):
                    self._advance()
                else:
                    self.errors.append(
                        CheckError(
                            self._current().line,
                            self._current().col,
                            "MS-E047",
                            "Expected property or method name after '.'",
                        )
                    )
                    return
            elif self._check(TokenType.LPAREN):
                self._parse_call_args()
            elif self._check(TokenType.LBRACKET):
                self._advance()
                self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after index")
            elif self._check(TokenType.COLON):
                # User property syntax: obj._property:name
                self._advance()
                if self._check(TokenType.IDENTIFIER):
                    self._advance()
                else:
                    self.errors.append(
                        CheckError(
                            self._current().line,
                            self._current().col,
                            "MS-E047",
                            "Expected property name after ':'",
                        )
                    )
                    return
            else:
                break

    def _parse_call_args(self) -> None:
        """Parse function call arguments."""
        self._advance()  # consume '('
        self._skip_comments()

        if not self._check(TokenType.RPAREN):
            self._parse_expression()
            while self._check(TokenType.COMMA):
                self._advance()
                self._skip_comments()
                if self._check(TokenType.RPAREN):
                    # Trailing comma - allowed
                    break
                self._parse_expression()

        self._expect(
            TokenType.RPAREN,  # pyrefly: ignore[unbound-name]
            "Expected ')' to close function call",
        )

    def _parse_primary(self) -> None:
        """Parse primary expression."""
        self._skip_comments()

        if self._check(TokenType.NUMBER, TokenType.STRING):
            self._advance()
        elif self._check(TokenType.TRUE, TokenType.FALSE, TokenType.NULL):
            self._advance()
        elif self._check(TokenType.IDENTIFIER):
            self._advance()
            # TODO: Track variable usage for undefined var checking
        elif self._check(TokenType.LPAREN):
            self._advance()
            self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
        elif self._check(TokenType.ERROR):
            # Already reported by tokenizer
            self._advance()
        else:
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-E048",
                    f"Unexpected token '{self._current().value}'",
                )
            )
            self._advance()

    def _recover_to_brace(self) -> None:
        """Skip tokens until we find a brace or EOF, then skip the block."""
        while not self._check(TokenType.LBRACE, TokenType.RBRACE, TokenType.EOF):
            self._advance()

        # If we hit a '{', skip the entire block
        if self._check(TokenType.LBRACE):
            self._skip_block()

    def _skip_block(self) -> None:
        """Skip a block including nested blocks."""
        if not self._check(TokenType.LBRACE):
            return

        self._advance()  # consume '{'
        depth = 1

        while depth > 0 and not self._check(TokenType.EOF):
            if self._check(TokenType.LBRACE):
                depth += 1
            elif self._check(TokenType.RBRACE):
                depth -= 1
            self._advance()


def check_method_body(
    body: str,
    method_name: str = "",
    start_line: int = 1,
    start_col: int = 1,
    parameters: list[str] | None = None,
    global_vars: set[str] | None = None,
) -> list[CheckError]:
    """Check a method body for errors.

    Args:
        body: The method body content (without the outer quotes)
        method_name: Name of the method
        start_line: Line number where body starts
        start_col: Column where body starts
        parameters: List of parameter names
        global_vars: Set of global variable names

    Returns:
        List of check errors
    """
    # Tokenize
    tokenizer = MethodBodyTokenizer(body, start_line, start_col)
    tokens = list(tokenizer.tokenize())

    # Collect tokenizer errors
    errors = list(tokenizer.errors)

    # Build set of defined variables
    defined = set(parameters or [])
    if global_vars:
        defined |= global_vars

    # Parse and check
    checker = MethodBodyChecker(tokens, method_name, defined)
    errors.extend(checker.check())

    return errors
