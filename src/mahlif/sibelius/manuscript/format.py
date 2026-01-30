"""ManuScript code formatter.

Provides opinionated, zero-config formatting for ManuScript plugin files.

Style rules:
- 4-space indentation
- Same-line braces: `if (x) {`
- Space after keywords: `if (`, `for (`, `while (`
- Space around binary operators: `x = 1 + 2`
- No trailing whitespace
- One statement per line
- Blank line between methods at plugin level
"""

from __future__ import annotations

import re
from pathlib import Path

from .tokens import Token
from .tokens import TokenType

# Indentation
INDENT = "    "  # 4 spaces

# Keywords that are followed by (
PAREN_KEYWORDS = {"if", "while", "for", "switch", "case"}


def format_file(path: Path) -> str:
    """Format a ManuScript plugin file.

    Args:
        path: Path to plugin file

    Returns:
        Formatted content
    """
    content = path.read_text(encoding="utf-8")
    # Strip BOM if present
    if content.startswith("\ufeff"):
        content = content[1:]
    return format_plugin(content)


def format_plugin(content: str) -> str:
    """Format plugin content.

    Args:
        content: Plugin file content

    Returns:
        Formatted content
    """
    lines = content.split("\n")
    result: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Opening brace - start of plugin
        if stripped == "{":
            result.append("{")
            i += 1
            continue

        # Closing brace - end of plugin
        if stripped == "}":
            result.append("}")
            i += 1
            continue

        # Empty line - preserve one between members
        if not stripped:
            # Only add blank line if we have content and last isn't blank
            if result and result[-1] != "":
                result.append("")
            i += 1
            continue

        # Comment line
        if stripped.startswith("//"):
            result.append(INDENT + stripped)
            i += 1
            continue

        # Member definition: Name "..."
        member_match = re.match(r'^(\s*)(\w+)\s+"', line)
        if member_match:
            name = member_match.group(2)
            # Find the string content
            quote_start = line.index('"')

            # Find matching end quote (handle multi-line strings)
            full_content = line[quote_start + 1 :]
            line_idx = i
            string_content: str | None = None
            while True:
                # Look for closing quote (not escaped)
                end_idx = _find_unescaped_quote(full_content)
                if end_idx >= 0:
                    string_content = full_content[:end_idx]
                    break
                # Continue to next line
                line_idx += 1
                if line_idx >= len(lines):
                    # Unterminated string - just pass through
                    result.append(line.rstrip())
                    i += 1
                    break
                full_content += "\n" + lines[line_idx]

            # If we broke out due to unterminated string, continue to next line
            if string_content is None:
                continue

            # Format the string content if it's a method body
            if string_content.strip().startswith("("):
                formatted_body = _format_method_body(string_content)
                result.append(INDENT + name + ' "' + formatted_body + '"')
            else:
                # Variable definition - just clean up whitespace
                result.append(INDENT + name + ' "' + string_content + '"')

            i = line_idx + 1
            continue

        # Unknown line - preserve
        result.append(line.rstrip())
        i += 1

    # Ensure trailing newline
    if result and result[-1] != "":
        result.append("")

    return "\n".join(result)


def _find_unescaped_quote(s: str) -> int:
    """Find first unescaped double quote in string.

    Args:
        s: String to search

    Returns:
        Index of quote, or -1 if not found
    """
    i = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2  # Skip escape sequence
        elif s[i] == '"':
            return i
        else:
            i += 1
    return -1


def _format_method_body(body: str) -> str:
    """Format a method body string.

    Args:
        body: Method body content like "(params) { statements }"

    Returns:
        Formatted body
    """
    # Parse out params and body content
    body = body.strip()
    if not body.startswith("("):
        return body

    # Find end of params
    paren_depth = 0
    paren_end = -1
    for i, c in enumerate(body):
        if c == "(":
            paren_depth += 1
        elif c == ")":
            paren_depth -= 1
            if paren_depth == 0:
                paren_end = i
                break

    if paren_end < 0:
        return body

    params = body[1:paren_end].strip()
    rest = body[paren_end + 1 :].strip()

    # Find the body content between { }
    if not rest.startswith("{"):
        return body

    brace_depth = 0
    brace_end = -1
    for i, c in enumerate(rest):
        if c == "{":
            brace_depth += 1
        elif c == "}":
            brace_depth -= 1
            if brace_depth == 0:
                brace_end = i
                break

    if brace_end < 0:
        return body

    inner = rest[1:brace_end].strip()

    # Format the inner content
    if not inner:
        # Empty body
        return f"({params}) {{ }}"

    formatted_inner = _format_statements(inner, base_indent=2)

    # Build result with proper newlines
    result = f"({params}) {{\n"
    result += formatted_inner
    result += "\n" + INDENT + "}"

    return result


def _format_statements(content: str, base_indent: int = 0) -> str:
    """Format a series of statements.

    Args:
        content: Statement content
        base_indent: Base indentation level

    Returns:
        Formatted statements
    """
    tokens = _tokenize_simple(content)

    lines: list[str] = []
    current_line: list[str] = []
    indent_level = base_indent

    def _space_before() -> None:
        """Add space before token if needed."""
        if current_line and not current_line[-1].endswith((" ", "(", ".", "[")):
            current_line.append(" ")

    def _strip_trailing_space() -> None:
        """Remove trailing space from current line."""
        if current_line and current_line[-1].endswith(" "):
            current_line[-1] = current_line[-1].rstrip()

    def _flush_line() -> None:
        """Flush current line to output."""
        nonlocal current_line
        if current_line:
            lines.append(_make_line(current_line, indent_level))
            current_line = []

    for i, tok in enumerate(tokens):
        # Peek at next token
        next_tok = tokens[i + 1] if i + 1 < len(tokens) else None

        match tok.type:
            # Structure tokens that affect indentation/lines
            case TokenType.LBRACE:
                current_line.append(" {")
                _flush_line()
                indent_level += 1

            case TokenType.RBRACE:
                _flush_line()
                indent_level -= 1
                # Keep "} else" on same line
                if next_tok and next_tok.type == TokenType.ELSE:
                    current_line.append("}")
                else:
                    lines.append(_make_line(["}"], indent_level))

            case TokenType.SEMICOLON:
                current_line.append(";")
                _flush_line()

            case TokenType.COMMENT:
                _space_before()
                current_line.append(tok.value)
                _flush_line()

            # Keywords with space after (take parentheses)
            case (
                TokenType.IF
                | TokenType.WHILE
                | TokenType.SWITCH
                | TokenType.CASE
                | TokenType.FOR
            ):
                _space_before()
                current_line.append(tok.value + " ")

            # Keywords without trailing space
            case (
                TokenType.ELSE
                | TokenType.RETURN
                | TokenType.DEFAULT
                | TokenType.EACH
                | TokenType.IN
                | TokenType.TO
            ):
                _space_before()
                current_line.append(tok.value)

            # Binary operators - space around
            case (
                TokenType.ASSIGN
                | TokenType.PLUS
                | TokenType.MINUS
                | TokenType.STAR
                | TokenType.SLASH
                | TokenType.LT
                | TokenType.GT
                | TokenType.LTE
                | TokenType.GTE
                | TokenType.NEQ
                | TokenType.AND
                | TokenType.OR
            ):
                current_line.append(f" {tok.value} ")

            # Comma - space after only
            case TokenType.COMMA:
                current_line.append(", ")

            # Parentheses - no extra space
            case TokenType.LPAREN:
                current_line.append("(")

            case TokenType.RPAREN:
                _strip_trailing_space()
                current_line.append(")")

            # Dot - no space around
            case TokenType.DOT:
                _strip_trailing_space()
                current_line.append(".")

            # Brackets - no extra space
            case TokenType.LBRACKET:
                current_line.append("[")

            case TokenType.RBRACKET:
                _strip_trailing_space()
                current_line.append("]")

            # Everything else (identifiers, literals, etc.)
            case _:
                _space_before()
                current_line.append(tok.value)

    # Flush remaining
    _flush_line()

    return "\n".join(lines)


def _make_line(parts: list[str], indent_level: int) -> str:
    """Build an indented line from parts."""
    content = "".join(parts).strip()
    if not content:
        return ""
    return (INDENT * indent_level) + content


def _tokenize_simple(content: str) -> list[Token]:
    """Simple tokenizer for formatting purposes.

    This is simpler than MethodBodyTokenizer - doesn't track errors,
    just produces tokens for reformatting.
    """
    from .tokenizer import MethodBodyTokenizer

    tokenizer = MethodBodyTokenizer(content)
    tokens = []
    for tok in tokenizer.tokenize():
        if tok.type != TokenType.EOF:
            tokens.append(tok)
    return tokens


def format_file_in_place(path: Path) -> bool:
    """Format a file in place.

    Args:
        path: Path to plugin file

    Returns:
        True if file was changed
    """
    original = path.read_text(encoding="utf-8")
    formatted = format_file(path)

    if original != formatted:
        path.write_text(formatted, encoding="utf-8")
        return True
    return False
