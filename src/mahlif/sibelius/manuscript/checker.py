"""Syntax and semantic checker for ManuScript method bodies.

This module parses tokenized method body content and checks for:
- Syntax errors (incomplete expressions, missing semicolons)
- Control flow validation (if/while/for/switch structure)
- Expression validation
- Undefined variable detection
- Undefined function/method detection
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import CheckError
from .tokenizer import MethodBodyTokenizer
from .tokenizer import Token
from .tokenizer import TokenType

LANG_JSON_PATH = Path(__file__).parent / "lang.json"


@dataclass
class FunctionSignature:
    """Signature info for argument count validation."""

    min_params: int
    max_params: int


def _load_lang_data() -> tuple[
    set[str],
    set[str],
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, list[FunctionSignature]],
    dict[str, dict[str, list[FunctionSignature]]],
]:
    """Load language data from lang.json.

    Returns:
        Tuple of (builtin_globals, builtin_functions, object_methods,
                  object_properties, builtin_signatures, method_signatures)

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
    builtin_signatures: dict[str, list[FunctionSignature]] = {}
    method_signatures: dict[str, dict[str, list[FunctionSignature]]] = {}

    # Add object type names and collect their methods/properties/signatures
    for obj_name, obj in data.get("objects", {}).items():
        globals_set.add(obj_name)
        object_methods[obj_name] = set(obj.get("methods", {}).keys())
        object_properties[obj_name] = set(obj.get("properties", []))

        # Extract method signatures
        method_signatures[obj_name] = {}
        for method_name, method_info in obj.get("methods", {}).items():
            sigs = []
            for sig in method_info.get("signatures", []):
                sigs.append(
                    FunctionSignature(
                        min_params=sig.get("min_params", 0),
                        max_params=sig.get("max_params", 0),
                    )
                )
            if sigs:  # pragma: no branch - lang.json methods always have signatures
                method_signatures[obj_name][method_name] = sigs

    # Add built-in functions and their signatures
    for name, info in data.get("builtin_functions", {}).items():
        globals_set.add(name)
        builtin_functions.add(name)

        # Parse params list - count required vs optional (ending with ?)
        params = info.get("params", [])
        min_params = sum(1 for p in params if not p.endswith("?"))
        max_params = len(params)
        builtin_signatures[name] = [FunctionSignature(min_params, max_params)]

    # Add all constants
    for name in data.get("constants", {}):
        globals_set.add(name)

    return (
        globals_set,
        builtin_functions,
        object_methods,
        object_properties,
        builtin_signatures,
        method_signatures,
    )


# Load at module import time
(
    BUILTIN_GLOBALS,
    BUILTIN_FUNCTIONS,
    OBJECT_METHODS,
    OBJECT_PROPERTIES,
    BUILTIN_SIGNATURES,
    METHOD_SIGNATURES,
) = _load_lang_data()


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
        # Track variable assignments and usages for unused variable detection
        self.var_assignments: dict[str, Token] = {}  # name -> first assignment token
        self.var_usages: set[str] = set()  # names that have been read
        # Track return seen for unreachable code detection
        self.return_seen: bool = False
        self.unreachable_warned: bool = False  # Only warn once per block
        # Track whether we're at statement level (vs inside expression)
        # Only at statement level is `x = y` an assignment; inside expressions it's comparison
        self.in_statement_context: bool = False

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

        # Report unused variables (assigned but never read)
        for var_name, token in self.var_assignments.items():
            if var_name not in self.var_usages:
                # Skip loop variables - they're often not "used" in the body
                # but that's intentional
                if var_name in self.defined_vars:
                    continue  # Parameters should always be considered "used"
                self.errors.append(
                    CheckError(
                        token.line,
                        token.col,
                        "MS-W025",
                        f"Variable '{var_name}' is assigned but never used",
                    )
                )

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

        # Check for unreachable code after return
        match (self.return_seen, self.unreachable_warned):
            case (True, False):
                # Check if there's actual code (not just block end)
                if not self._check(  # pragma: no branch
                    TokenType.RBRACE, TokenType.EOF
                ):
                    self.errors.append(
                        CheckError(
                            self._current().line,
                            self._current().col,
                            "MS-W026",
                            "Unreachable code after return statement",
                        )
                    )
                    self.unreachable_warned = True
            case _:
                pass  # No return seen, or already warned

        # Control flow statements - dispatch based on current token type
        match self._current().type:
            case TokenType.IF:
                self._parse_if()
            case TokenType.WHILE:
                self._parse_while()
            case TokenType.FOR:
                self._parse_for()
            case TokenType.SWITCH:
                self._parse_switch()
            case TokenType.RETURN:
                self._parse_return()
            case TokenType.LBRACE:
                self._parse_block()
            case TokenType.RBRACE:
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
            case TokenType.SEMICOLON:
                # Empty statement - warn about it
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-W030",
                        "Empty statement (lone ';')",
                    )
                )
                self._advance()
            case TokenType.EOF:  # pragma: no cover - main loop catches EOF first
                pass
            case _:
                # Expression statement (assignment or call)
                self._parse_expression_statement()

    def _parse_if(self) -> None:
        """Parse if statement."""
        self._advance()  # consume 'if'

        # Expect (
        if not self._expect(TokenType.LPAREN, "Expected '(' after 'if'"):
            self._recover_to_brace()
            return

        # Check for constant condition before parsing
        self._skip_comments()
        self._check_constant_condition("if")

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
                # Loop variables are implicitly used
                self.var_usages.add(var_token.value)
            elif self._check(TokenType.IN):
                # Just var, no type
                self.local_vars.add(first_ident.value)
                # Loop variables are implicitly used
                self.var_usages.add(first_ident.value)
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
        # Track loop variable assignment (but mark as used since loop vars are implicitly used)
        self.var_usages.add(var_token.value)

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

    def _check_constant_condition(self, context: str) -> None:
        """Check if condition is a constant (True, False, number).

        Args:
            context: Where this condition appears (for error message)
        """
        # Only warn for 'if', not 'while' (constant while is common pattern)
        if context != "if":  # pragma: no cover - currently only called with "if"
            return

        # Check if next token is a constant
        if self._check(TokenType.TRUE):
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-W028",
                    "Condition is always true; 'else' branch will never execute",
                )
            )
        elif self._check(TokenType.FALSE):
            self.errors.append(
                CheckError(
                    self._current().line,
                    self._current().col,
                    "MS-W028",
                    "Condition is always false; 'if' body will never execute",
                )
            )
        elif self._check(TokenType.NUMBER):
            value = self._current().value
            if value == "0":
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-W028",
                        "Condition is always false (0); 'if' body will never execute",
                    )
                )
            else:
                self.errors.append(
                    CheckError(
                        self._current().line,
                        self._current().col,
                        "MS-W028",
                        f"Condition is always true ({value}); 'else' branch will never execute",
                    )
                )

    def _parse_return(self) -> None:
        """Parse return statement."""
        self._advance()  # consume 'return'
        self._skip_comments()

        # Optional return value
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            self._parse_expression()

        self._expect(TokenType.SEMICOLON, "Expected ';' after return statement")

        # Mark that we've seen a return for unreachable code detection
        self.return_seen = True

    def _parse_block(self) -> None:
        """Parse a block { statements }."""
        self._advance()  # consume '{'

        # Save and reset return tracking for this block
        outer_return_seen = self.return_seen
        outer_unreachable_warned = self.unreachable_warned
        self.return_seen = False
        self.unreachable_warned = False

        while not self._check(TokenType.RBRACE, TokenType.EOF):
            self._parse_statement()
            self._skip_comments()

        self._expect(TokenType.RBRACE, "Expected '}' to close block")

        # Restore outer block's tracking
        self.return_seen = outer_return_seen
        self.unreachable_warned = outer_unreachable_warned

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
        # At statement level, `x = y;` is assignment. Inside expressions, it's comparison.
        self.in_statement_context = True
        self._parse_expression()
        self.in_statement_context = False
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
                # Only treat as assignment if we're at statement level
                # Inside expressions (if, while, etc.), = is comparison
                if next_tok.type == TokenType.ASSIGN and self.in_statement_context:
                    # Pre-register this variable as defined
                    var_name = self._current().value
                    var_token = self._current()

                    # Check for variable shadowing (local shadows parameter)
                    if (
                        var_name in self.defined_vars
                        and var_name not in self.local_vars
                    ):
                        self.errors.append(
                            CheckError(
                                var_token.line,
                                var_token.col,
                                "MS-W033",
                                f"Variable '{var_name}' shadows a parameter",
                            )
                        )

                    self.local_vars.add(var_name)
                    # Track assignment location for unused variable warning
                    if var_name not in self.var_assignments:
                        self.var_assignments[var_name] = var_token

                    # Check for self-assignment: x = x;
                    # Peek: pos is at IDENT, pos+1 is =, pos+2 would be RHS
                    if self.pos + 3 < len(self.tokens):
                        rhs_tok = self.tokens[self.pos + 2]
                        after_rhs = self.tokens[self.pos + 3]
                        if (
                            rhs_tok.type == TokenType.IDENTIFIER
                            and rhs_tok.value == var_name
                            and after_rhs.type == TokenType.SEMICOLON
                        ):
                            self.errors.append(
                                CheckError(
                                    var_token.line,
                                    var_token.col,
                                    "MS-W029",
                                    f"Self-assignment '{var_name} = {var_name}' has no effect",
                                )
                            )

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
        # Track position before LHS for comparison-to-self detection
        lhs_start = self.pos
        self._parse_additive()
        lhs_end = self.pos

        while self._check(
            TokenType.ASSIGN,
            TokenType.NEQ,
            TokenType.LT,
            TokenType.GT,
            TokenType.LTE,
            TokenType.GTE,
        ):
            op_token = self._advance()
            rhs_start = self.pos
            self._parse_additive()
            rhs_end = self.pos

            # Check for comparison to self: simple IDENT op IDENT
            if lhs_end - lhs_start == 1 and rhs_end - rhs_start == 1:
                lhs_tok = self.tokens[lhs_start]
                rhs_tok = self.tokens[rhs_start]
                if (
                    lhs_tok.type == TokenType.IDENTIFIER
                    and rhs_tok.type == TokenType.IDENTIFIER
                    and lhs_tok.value == rhs_tok.value
                ):
                    match op_token.type:
                        case TokenType.ASSIGN | TokenType.LTE | TokenType.GTE:
                            op_str = {
                                TokenType.ASSIGN: "=",
                                TokenType.LTE: "<=",
                                TokenType.GTE: ">=",
                            }[op_token.type]
                            self.errors.append(
                                CheckError(
                                    op_token.line,
                                    op_token.col,
                                    "MS-W032",
                                    f"Comparison '{lhs_tok.value} {op_str} {lhs_tok.value}' is always true",
                                )
                            )
                        case TokenType.NEQ | TokenType.LT | TokenType.GT:
                            op_str = {
                                TokenType.NEQ: "!=",
                                TokenType.LT: "<",
                                TokenType.GT: ">",
                            }[op_token.type]
                            self.errors.append(
                                CheckError(
                                    op_token.line,
                                    op_token.col,
                                    "MS-W032",
                                    f"Comparison '{lhs_tok.value} {op_str} {lhs_tok.value}' is always false",
                                )
                            )
                        case _:  # pragma: no cover
                            pass  # Other token types can't reach here

            # Update for next iteration
            lhs_start, lhs_end = rhs_start, rhs_end

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
            op_token = self._advance()
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
            # Check for division/modulo by zero
            if op_token.type in (TokenType.SLASH, TokenType.PERCENT):
                if self._check(TokenType.NUMBER) and self._current().value == "0":
                    op_name = (
                        "Division" if op_token.type == TokenType.SLASH else "Modulo"
                    )
                    self.errors.append(
                        CheckError(
                            self._current().line,
                            self._current().col,
                            "MS-W031",
                            f"{op_name} by zero",
                        )
                    )
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
                    # If next token is NOT '(', this was property access
                    self._skip_comments()
                    if not self._check(TokenType.LPAREN) and had_receiver:
                        # Check if property exists on receiver
                        self._check_property(
                            receiver_type, last_identifier, last_identifier_token
                        )
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
                # This is a function/method call - parse args first to get count
                arg_count = self._parse_call_args()
                self._check_call(
                    receiver_type, last_identifier, last_identifier_token, arg_count
                )
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
        arg_count: int = 0,
    ) -> None:
        """Check if a function/method call is valid.

        Args:
            receiver_type: Known object type (e.g., "Sibelius") or None
            method_name: Name of the method/function being called
            token: Token for error reporting
            arg_count: Number of arguments passed
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
            else:
                # Check argument count
                self._check_arg_count(receiver_type, method_name, arg_count, token)
            return

        # Case 2: Bare function call (e.g., Foo())
        # Check if it's a builtin function
        if method_name in BUILTIN_FUNCTIONS:
            self._check_arg_count(None, method_name, arg_count, token)
            return

        # Check if it's a method defined in the same plugin
        if method_name in self.plugin_methods:
            return  # Can't check arg count for plugin methods

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

    def _check_arg_count(
        self,
        receiver_type: str | None,
        method_name: str,
        arg_count: int,
        token: Token,
    ) -> None:
        """Check if argument count matches function signature.

        Args:
            receiver_type: Object type or None for builtin
            method_name: Name of the function/method
            arg_count: Number of arguments passed
            token: Token for error reporting
        """
        signatures: list[FunctionSignature] = []

        if receiver_type is not None:
            # Method on known object
            obj_sigs = METHOD_SIGNATURES.get(receiver_type, {})
            signatures = obj_sigs.get(method_name, [])
        else:
            # Builtin function
            signatures = BUILTIN_SIGNATURES.get(method_name, [])

        if not signatures:
            return  # No signature info available

        # Check if arg_count matches any signature
        for sig in signatures:
            if sig.min_params <= arg_count <= sig.max_params:
                return  # Valid

        # Build error message
        if len(signatures) == 1:
            sig = signatures[0]
            if sig.min_params == sig.max_params:
                expected = f"{sig.min_params}"
            else:
                expected = f"{sig.min_params}-{sig.max_params}"
        else:
            # Multiple overloads - show all valid ranges
            ranges = []
            for sig in signatures:
                if sig.min_params == sig.max_params:
                    ranges.append(str(sig.min_params))
                else:
                    ranges.append(f"{sig.min_params}-{sig.max_params}")
            expected = " or ".join(ranges)

        self.errors.append(
            CheckError(
                token.line,
                token.col,
                "MS-W023",
                f"'{method_name}' expects {expected} argument(s), got {arg_count}",
            )
        )

    def _check_property(
        self,
        receiver_type: str | None,
        prop_name: str,
        token: Token,
    ) -> None:
        """Check if a property access is valid.

        Args:
            receiver_type: Object type (e.g., "Sibelius") or None
            prop_name: Name of the property being accessed
            token: Token for error reporting
        """
        if receiver_type is None:
            return

        properties = OBJECT_PROPERTIES.get(receiver_type, set())
        methods = OBJECT_METHODS.get(receiver_type, set())

        # Property exists
        if prop_name in properties:
            return

        # Could be a method being accessed without call (e.g., for passing as ref)
        if prop_name in methods:
            return

        # Property not found - suggest similar names
        all_members = properties | methods
        suggestion = self._find_similar(prop_name, all_members)

        msg = f"Property '{prop_name}' not found on '{receiver_type}'"
        if suggestion:
            msg += f"; did you mean '{suggestion}'?"

        self.errors.append(CheckError(token.line, token.col, "MS-W024", msg))

    def _find_similar(self, name: str, candidates: set[str]) -> str | None:
        """Find the most similar name from candidates.

        Uses simple edit distance (Levenshtein) to find closest match.

        Args:
            name: The misspelled name
            candidates: Set of valid names

        Returns:
            Most similar name if close enough, else None
        """
        if not candidates:
            return None

        def edit_distance(s1: str, s2: str) -> int:
            """Compute Levenshtein distance between two strings."""
            if len(s1) < len(s2):
                return edit_distance(s2, s1)

            if len(s2) == 0:
                return len(s1)

            prev_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                curr_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = prev_row[j + 1] + 1
                    deletions = curr_row[j] + 1
                    substitutions = prev_row[j] + (c1 != c2)
                    curr_row.append(min(insertions, deletions, substitutions))
                prev_row = curr_row

            return prev_row[-1]

        # Find closest match
        best_match = None
        best_distance = float("inf")
        name_lower = name.lower()

        for candidate in candidates:
            # Quick check for case-insensitive match
            if candidate.lower() == name_lower:
                return candidate

            dist = edit_distance(name.lower(), candidate.lower())
            if dist < best_distance:
                best_distance = dist
                best_match = candidate

        # Only suggest if distance is reasonable (less than 40% of name length)
        max_distance = max(2, int(len(name) * 0.4))
        if best_distance <= max_distance:
            return best_match

        return None

    def _parse_call_args(self) -> int:
        """Parse function call arguments.

        Returns:
            Number of arguments parsed
        """
        self._advance()  # consume '('
        self._skip_comments()

        arg_count = 0
        if not self._check(TokenType.RPAREN):
            self._parse_expression()
            arg_count = 1
            while self._check(TokenType.COMMA):
                self._advance()
                self._skip_comments()
                if self._check(TokenType.RPAREN):
                    # Trailing comma - allowed
                    break
                self._parse_expression()
                arg_count += 1

        self._expect(
            TokenType.RPAREN,  # pyrefly: ignore[unbound-name]
            "Expected ')' to close function call",
        )
        return arg_count

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

            # Track variable usage (read)
            # We mark as used UNLESS this is the very first token of an assignment
            # (detected by checking if var_name was just added to var_assignments)
            just_assigned = (
                var_name in self.var_assignments
                and self.var_assignments[var_name] == token
            )
            if not just_assigned:
                self.var_usages.add(var_name)

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


# Division/modulo by zero will be checked in binary operators
# Comparison to self will be checked in comparison operators
# These are inserted during expression parsing
