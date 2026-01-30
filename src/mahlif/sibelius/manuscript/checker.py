"""Syntax and semantic checker for ManuScript method bodies.

This module parses tokenized method body content and checks for:
- Syntax errors (incomplete expressions, missing semicolons)
- Control flow validation (if/while/for/switch structure)
- Expression validation
- Undefined variable detection
- Undefined function/method detection
"""

from __future__ import annotations

from .errors import CheckError
from .tokenizer import MethodBodyTokenizer
from .tokenizer import Token
from .tokenizer import TokenType

import json
from pathlib import Path

LANG_JSON_PATH = Path(__file__).parent / "lang.json"


def _load_lang_data() -> tuple[
    set[str], set[str], dict[str, set[str]], dict[str, set[str]]
]:
    """Load language data from lang.json.

    Returns:
        Tuple of (builtin_globals, builtin_functions, object_methods, object_properties)

    Raises:
        FileNotFoundError: If lang.json is missing
    """
    if not LANG_JSON_PATH.exists():
        raise FileNotFoundError(
            f"Required language data file not found: {LANG_JSON_PATH}\n"
            "Run: pdftotext 'ManuScript Language.pdf' - | python extract.py > lang.json"
        )

    with open(LANG_JSON_PATH) as f:
        data = json.load(f)

    globals_set: set[str] = set()
    builtin_functions: set[str] = set()
    object_methods: dict[str, set[str]] = {}
    object_properties: dict[str, set[str]] = {}

    # Add object type names and collect their methods/properties
    for name, obj in data.get("objects", {}).items():
        globals_set.add(name)
        object_methods[name] = set(obj.get("methods", {}).keys())
        object_properties[name] = set(obj.get("properties", []))

    # Add built-in functions
    for name in data.get("builtin_functions", {}):
        globals_set.add(name)
        builtin_functions.add(name)

    # Add all constants
    for name in data.get("constants", {}):
        globals_set.add(name)

    return globals_set, builtin_functions, object_methods, object_properties


# Load at module import time
BUILTIN_GLOBALS, BUILTIN_FUNCTIONS, OBJECT_METHODS, OBJECT_PROPERTIES = (
    _load_lang_data()
)


class MethodBodyChecker:
    """Check ManuScript method body for errors."""

    def __init__(
        self,
        tokens: list[Token],
        method_name: str = "",
        defined_vars: set[str] | None = None,
        plugin_methods: set[str] | None = None,
    ) -> None:
        """Initialize checker.

        Args:
            tokens: List of tokens from tokenizer
            method_name: Name of the method being checked
            defined_vars: Set of pre-defined variables (parameters, globals)
            plugin_methods: Set of method names defined in the same plugin
        """
        self.tokens = tokens
        self.method_name = method_name
        self.pos = 0
        self.errors: list[CheckError] = []
        self.defined_vars: set[str] = defined_vars or set()
        self.local_vars: set[str] = set()
        self.plugin_methods: set[str] = plugin_methods or set()

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
        return self.tokens[-1]  # pragma: no cover - defensive for pos past end

    def _check(self, *types: TokenType) -> bool:
        """Check if current token is one of the given types."""
        return self._current().type in types

    def _advance(self) -> Token:
        """Advance and return current token."""
        token = self._current()
        if self.pos < len(self.tokens) - 1:  # pragma: no branch - always true until EOF
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
            # Unexpected closing brace - report error and skip
            token = self._current()
            self.errors.append(
                CheckError(
                    token.line,
                    token.col,
                    "MS-E001",
                    "Unexpected '}'",
                )
            )
            self._advance()
            return
        elif self._check(TokenType.SEMICOLON):
            # Empty statement
            self._advance()
        elif self._check(
            TokenType.EOF
        ):  # pragma: no cover - main loop catches EOF first
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
            elif self._check(TokenType.RBRACE, TokenType.EOF):
                # Exit early if we hit end of switch (can happen after _skip_comments)
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
        # Check if this looks like a simple assignment: IDENTIFIER = ...
        # Add the target to local_vars BEFORE parsing so we don't warn about it
        if self._check(TokenType.IDENTIFIER):
            # Peek ahead to see if this is an assignment.
            # Tokenizer always produces EOF as last token, so pos+1 < len is always true.
            if self.pos + 1 < len(self.tokens):  # pragma: no branch
                next_tok = self.tokens[self.pos + 1]
                if next_tok.type == TokenType.ASSIGN:
                    # Pre-register this variable as defined
                    self.local_vars.add(self._current().value)

        # Parse left side
        self._parse_or_expr()
        self._skip_comments()

        # Check for assignment.
        # NOTE: This block is currently unreachable because _parse_or_expr()
        # consumes '=' as an equality operator. ManuScript uses '=' for both
        # assignment and equality. Keeping as defensive code.
        if self._check(TokenType.ASSIGN):  # pragma: no cover
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
        # Track the receiver for method call checking
        # receiver_type is the known object type (e.g., "Sibelius"), or None
        # Only set if followed by '.' to avoid false positives on Sibelius() bare calls
        receiver_type: str | None = None
        last_identifier: str | None = None
        last_identifier_token: Token | None = None

        # Check if primary is a known object type followed by '.'
        if self._check(TokenType.IDENTIFIER):
            name = self._current().value
            last_identifier = name
            last_identifier_token = self._current()
            # Peek ahead - only set receiver_type if followed by '.'
            if self.pos + 1 < len(self.tokens) - 1:  # pragma: no branch
                next_tok = self.tokens[self.pos + 1]
                if next_tok.type == TokenType.DOT and name in OBJECT_METHODS:
                    receiver_type = name

        self._parse_primary()

        while True:
            self._skip_comments()
            if self._check(TokenType.DOT):
                # After property access, we lose type info unless we track return types
                # Keep receiver_type only for immediate method call (Sibelius.Foo())
                # but reset if we're accessing a property first (Sibelius.ActiveScore.Foo())
                had_receiver = receiver_type is not None
                self._advance()
                self._skip_comments()
                if self._check(TokenType.IDENTIFIER):
                    last_identifier = self._current().value
                    last_identifier_token = self._current()
                    self._advance()
                    # If next token is NOT '(', this was property access, lose type
                    self._skip_comments()
                    if not self._check(TokenType.LPAREN) and had_receiver:
                        receiver_type = None
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
                # This is a function/method call
                self._check_call(receiver_type, last_identifier, last_identifier_token)
                self._parse_call_args()
                # After a call, we don't know the type anymore
                receiver_type = None
                last_identifier = None
                last_identifier_token = None
            elif self._check(TokenType.LBRACKET):
                self._advance()
                self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after index")
                # After indexing, type is unknown
                receiver_type = None
                last_identifier = None
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
                receiver_type = None
                last_identifier = None
            else:
                break

    def _check_call(
        self,
        receiver_type: str | None,
        method_name: str | None,
        token: Token | None,
    ) -> None:
        """Check if a function/method call is valid.

        Args:
            receiver_type: Known object type (e.g., "Sibelius") or None
            method_name: Name of the method/function being called
            token: Token for error reporting
        """
        if method_name is None or token is None:
            return

        # Case 1: Known receiver type (e.g., Sibelius.Foo())
        if receiver_type is not None:
            methods = OBJECT_METHODS.get(receiver_type, set())
            if method_name not in methods:
                self.errors.append(
                    CheckError(
                        token.line,
                        token.col,
                        "MS-W022",
                        f"Method '{method_name}' not found on '{receiver_type}'",
                    )
                )
            return

        # Case 2: Bare function call (e.g., Foo())
        # Check if it's a builtin function
        if method_name in BUILTIN_FUNCTIONS:
            return

        # Check if it's a method defined in the same plugin
        if method_name in self.plugin_methods:
            return

        # Check if it's a known object type being called as constructor
        # (ManuScript doesn't have constructors, but we allow it)
        if method_name in OBJECT_METHODS:
            return

        # Check if it's a method on Self
        # Note: Self currently has no methods in lang.json, but kept for future
        self_methods = OBJECT_METHODS.get("Self", set())
        if method_name in self_methods:  # pragma: no cover
            return

        # Check if it could be a method call on an unknown receiver
        # If the method exists on ANY object, don't warn (could be valid)
        for obj_methods in OBJECT_METHODS.values():
            if method_name in obj_methods:
                return

        # Unknown function - warn
        self.errors.append(
            CheckError(
                token.line,
                token.col,
                "MS-W022",
                f"Function '{method_name}' is not a known builtin or method",
            )
        )

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
            token = self._advance()
            var_name = token.value
            # Check if variable is defined
            if (
                var_name not in self.defined_vars
                and var_name not in self.local_vars
                and var_name not in BUILTIN_GLOBALS
            ):
                # Only warn if it's not followed by ( - could be a method call
                # or followed by . - could be an object access
                if not self._check(TokenType.LPAREN, TokenType.DOT):
                    self.errors.append(
                        CheckError(
                            token.line,
                            token.col,
                            "MS-W020",
                            f"Variable '{var_name}' may be undefined",
                        )
                    )
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
        if self._check(
            TokenType.LBRACE
        ):  # pragma: no branch - recovery typically hits RBRACE/EOF
            self._skip_block()

    def _skip_block(self) -> None:
        """Skip a block including nested blocks."""
        if not self._check(
            TokenType.LBRACE
        ):  # pragma: no cover - only called when at LBRACE
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
    plugin_methods: set[str] | None = None,
) -> list[CheckError]:
    """Check a method body for errors.

    Args:
        body: The method body content (without the outer quotes)
        method_name: Name of the method
        start_line: Line number where body starts
        start_col: Column where body starts
        parameters: List of parameter names
        global_vars: Set of global variable names
        plugin_methods: Set of method names defined in the same plugin

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
    checker = MethodBodyChecker(tokens, method_name, defined, plugin_methods)
    errors.extend(checker.check())

    return errors
