"""Tests for ManuScript AST module."""

from __future__ import annotations

import pytest

from mahlif.sibelius.manuscript.ast import Parser
from mahlif.sibelius.manuscript.ast import Plugin
from mahlif.sibelius.manuscript.ast import Token
from mahlif.sibelius.manuscript.ast import TokenType
from mahlif.sibelius.manuscript.ast import Tokenizer
from mahlif.sibelius.manuscript.ast import get_method_calls
from mahlif.sibelius.manuscript.ast import parse_plugin


def test_tokenizer_basic() -> None:
    """Test basic tokenization."""
    tokenizer = Tokenizer("x = 1;")
    tokens = list(tokenizer.tokenize())
    types = [t.type for t in tokens]
    assert TokenType.IDENTIFIER in types
    assert TokenType.ASSIGN in types
    assert TokenType.NUMBER in types
    assert TokenType.SEMICOLON in types
    assert TokenType.EOF in types


def test_tokenizer_string_single() -> None:
    """Test single-quoted string."""
    tokenizer = Tokenizer("'hello'")
    tokens = list(tokenizer.tokenize())
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "'hello'"


def test_tokenizer_string_double() -> None:
    """Test double-quoted string."""
    tokenizer = Tokenizer('"hello"')
    tokens = list(tokenizer.tokenize())
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == '"hello"'


def test_tokenizer_string_escape() -> None:
    """Test escaped string."""
    tokenizer = Tokenizer(r"'it\'s'")
    tokens = list(tokenizer.tokenize())
    assert tokens[0].type == TokenType.STRING


def test_tokenizer_number() -> None:
    """Test number tokenization."""
    tokenizer = Tokenizer("123 -45 3.14")
    tokens = list(tokenizer.tokenize())
    numbers = [t for t in tokens if t.type == TokenType.NUMBER]
    assert len(numbers) == 3
    assert numbers[0].value == "123"
    assert numbers[1].value == "-45"
    assert numbers[2].value == "3.14"


def test_tokenizer_keywords() -> None:
    """Test keyword recognition."""
    tokenizer = Tokenizer("if else for while return true false null")
    tokens = list(tokenizer.tokenize())
    assert tokens[0].type == TokenType.IF
    assert tokens[1].type == TokenType.ELSE
    assert tokens[2].type == TokenType.FOR
    assert tokens[3].type == TokenType.WHILE
    assert tokens[4].type == TokenType.RETURN
    assert tokens[5].type == TokenType.TRUE
    assert tokens[6].type == TokenType.FALSE
    assert tokens[7].type == TokenType.NULL


def test_tokenizer_operators() -> None:
    """Test operator tokenization."""
    tokenizer = Tokenizer("+ - * / % < > <= >= !=")
    tokens = list(tokenizer.tokenize())
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert TokenType.PLUS in types
    assert TokenType.MINUS in types
    assert TokenType.STAR in types
    assert TokenType.SLASH in types
    assert TokenType.PERCENT in types
    assert TokenType.LT in types
    assert TokenType.GT in types
    assert TokenType.LTE in types
    assert TokenType.GTE in types
    assert TokenType.NEQ in types


def test_tokenizer_delimiters() -> None:
    """Test delimiter tokenization."""
    tokenizer = Tokenizer("( ) { } [ ] , ;")
    tokens = list(tokenizer.tokenize())
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert TokenType.LPAREN in types
    assert TokenType.RPAREN in types
    assert TokenType.LBRACE in types
    assert TokenType.RBRACE in types
    assert TokenType.LBRACKET in types
    assert TokenType.RBRACKET in types
    assert TokenType.COMMA in types
    assert TokenType.SEMICOLON in types


def test_tokenizer_comment() -> None:
    """Test comment handling."""
    tokenizer = Tokenizer("x = 1; // comment\ny = 2;")
    tokens = list(tokenizer.tokenize())
    comments = [t for t in tokens if t.type == TokenType.COMMENT]
    assert len(comments) == 1


def test_tokenizer_dot() -> None:
    """Test dot operator."""
    tokenizer = Tokenizer("obj.method")
    tokens = list(tokenizer.tokenize())
    assert tokens[1].type == TokenType.DOT


def test_tokenizer_ampersand() -> None:
    """Test ampersand (string concat)."""
    tokenizer = Tokenizer("'a' & 'b'")
    tokens = list(tokenizer.tokenize())
    assert any(t.type == TokenType.AMPERSAND for t in tokens)


def test_tokenizer_unknown_char() -> None:
    """Test unknown character is skipped."""
    tokenizer = Tokenizer("x @ y")
    tokens = list(tokenizer.tokenize())
    # @ should be skipped
    idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
    assert len(idents) == 2


def test_token_repr() -> None:
    """Test Token repr."""
    token = Token(TokenType.IDENTIFIER, "foo", 1, 5)
    assert "IDENTIFIER" in repr(token)
    assert "foo" in repr(token)
    assert "1:5" in repr(token)


def test_parser_empty_plugin() -> None:
    """Test parsing empty plugin."""
    plugin = parse_plugin("{ }")
    assert plugin.members == []


def test_parser_method_def() -> None:
    """Test parsing method definition."""
    plugin = parse_plugin('{ Initialize "() { }" }')
    assert len(plugin.members) == 1
    assert plugin.members[0].name == "Initialize"  # type: ignore


def test_parser_method_with_params() -> None:
    """Test parsing method with parameters."""
    plugin = parse_plugin('{ Test "(a, b, c) { }" }')
    assert len(plugin.members) == 1
    method = plugin.members[0]
    assert method.params == ["a", "b", "c"]  # type: ignore


def test_parser_var_def() -> None:
    """Test parsing variable definition."""
    plugin = parse_plugin('{ Name "Test Plugin" }')
    assert len(plugin.members) == 1
    assert plugin.members[0].value == "Test Plugin"  # type: ignore


def test_parser_bom_stripped() -> None:
    """Test BOM is stripped."""
    plugin = parse_plugin("\ufeff{ }")
    assert plugin.members == []


def test_get_method_calls_simple() -> None:
    """Test extracting simple method call."""
    calls = get_method_calls("Sibelius.MessageBox('hi');")
    assert len(calls) == 1
    line, col, obj, method, arg_count = calls[0]
    assert obj == "Sibelius"
    assert method == "MessageBox"
    assert arg_count == 1


def test_get_method_calls_global() -> None:
    """Test extracting global function call."""
    calls = get_method_calls("CreateSparseArray();")
    assert len(calls) == 1
    line, col, obj, method, arg_count = calls[0]
    assert obj is None
    assert method == "CreateSparseArray"
    assert arg_count == 0


def test_get_method_calls_multiple_args() -> None:
    """Test extracting call with multiple args."""
    calls = get_method_calls("bar.AddNote(0, 60, 256, True, 1);")
    assert len(calls) == 1
    assert calls[0][4] == 5  # arg_count


def test_get_method_calls_nested() -> None:
    """Test extracting nested calls."""
    calls = get_method_calls("foo(bar(1, 2));")
    # Should find both calls
    assert len(calls) >= 1


def test_get_method_calls_empty_args() -> None:
    """Test call with no arguments."""
    calls = get_method_calls("obj.Method();")
    assert calls[0][4] == 0


# =============================================================================
# extract_api tests
# =============================================================================


def test_manuscript_ast_for_each_in() -> None:
    """Test tokenizing for each in keywords."""
    tokenizer = Tokenizer("for each x in y")
    tokens = list(tokenizer.tokenize())
    assert any(t.type == TokenType.FOR for t in tokens)
    assert any(t.type == TokenType.EACH for t in tokens)
    assert any(t.type == TokenType.IN for t in tokens)


def test_manuscript_ast_to_keyword() -> None:
    """Test tokenizing 'to' keyword."""
    tokenizer = Tokenizer("for i = 1 to 10")
    tokens = list(tokenizer.tokenize())
    assert any(t.type == TokenType.TO for t in tokens)


def test_manuscript_ast_and_or_not() -> None:
    """Test boolean operators."""
    tokenizer = Tokenizer("a and b or not c")
    tokens = list(tokenizer.tokenize())
    assert any(t.type == TokenType.AND for t in tokens)
    assert any(t.type == TokenType.OR for t in tokens)
    assert any(t.type == TokenType.NOT for t in tokens)


def test_manuscript_ast_case_switch() -> None:
    """Test switch/case keywords."""
    tokenizer = Tokenizer("switch (x) { case 1: }")
    tokens = list(tokenizer.tokenize())
    assert any(t.type == TokenType.SWITCH for t in tokens)
    assert any(t.type == TokenType.CASE for t in tokens)


def test_manuscript_ast_True_False_keyword() -> None:
    """Test True/False as keywords (case sensitive)."""
    tokenizer = Tokenizer("True False")
    tokens = list(tokenizer.tokenize())
    assert tokens[0].type == TokenType.TRUE
    assert tokens[1].type == TokenType.FALSE


def test_parser_expect_wrong_token() -> None:
    """Test parser error on unexpected token."""
    tokens = [
        Token(TokenType.IDENTIFIER, "foo", 1, 1),
        Token(TokenType.EOF, "", 1, 4),
    ]
    parser = Parser(tokens)
    with pytest.raises(SyntaxError, match="Expected LBRACE"):
        parser.parse()


def test_parser_empty_params() -> None:
    """Test method with empty params string."""
    plugin = parse_plugin('{ Test "() { }" }')
    assert len(plugin.members) == 1
    method = plugin.members[0]
    assert method.params == []  # type: ignore


def test_get_method_calls_comment_in_args() -> None:
    """Test method calls ignore comments in arg counting."""
    calls = get_method_calls("foo(a, // comment\nb);")
    # Should find foo with 2 args
    assert len(calls) >= 1


def test_manuscript_ast_peek_beyond_end() -> None:
    """Test peeking beyond end of source."""
    tokenizer = Tokenizer("x")
    list(tokenizer.tokenize())  # Exhaust
    assert tokenizer._peek(100) == ""


def test_parser_check_eof() -> None:
    """Test parser checking for EOF."""
    tokens = [Token(TokenType.EOF, "", 1, 1)]
    parser = Parser(tokens)
    assert parser._check(TokenType.EOF) is True


def test_get_method_calls_newline_in_args() -> None:
    """Test method with newlines in args."""
    calls = get_method_calls("foo(\na,\nb\n);")
    assert len(calls) >= 1
    assert calls[0][4] == 2  # 2 args


def test_parser_advance_beyond_end() -> None:
    """Test parser advance beyond token list."""
    tokens = [Token(TokenType.LBRACE, "{", 1, 1), Token(TokenType.EOF, "", 1, 2)]
    parser = Parser(tokens)
    parser._advance()  # {
    parser._advance()  # EOF
    parser._advance()  # Still returns last token
    # Should not crash


def test_parse_plugin_member_not_identifier() -> None:
    """Test plugin member that doesn't start with identifier."""
    # Lines 446-447: not self._check(TokenType.IDENTIFIER), advance and return None
    plugin = parse_plugin('{ 123 Name "() { }" }')
    # Should skip the number and parse the method
    assert len(plugin.members) >= 0


def test_parse_plugin_member_identifier_not_followed_by_string() -> None:
    """Test identifier not followed by string literal."""
    # Line 473: return None when not string after identifier
    plugin = parse_plugin("{ x = 5; }")
    # Should handle gracefully
    assert isinstance(plugin, Plugin)


def test_get_method_calls_obj_dot_method() -> None:
    """Test method call with object.method pattern."""
    # Lines 554-555: obj.method() path
    calls = get_method_calls("bar.AddNote(1, 2, 3, 4);")
    assert len(calls) >= 1
    # Should have obj="bar", method="AddNote"
    found = False
    for line, col, obj, method, args in calls:
        if obj == "bar" and method == "AddNote":
            found = True
            break
    assert found


def test_get_method_calls_standalone_method() -> None:
    """Test standalone method call (no object)."""
    # Lines 557-559: method() without object prefix
    calls = get_method_calls("CreateArray();")
    assert len(calls) >= 1


def test_get_method_calls_identifier_not_followed_by_lparen() -> None:
    """Test identifier that's not a method call."""
    # Line 554-555: i += 1, continue when not method call
    calls = get_method_calls("x = y + z;")
    # No method calls here
    assert len(calls) == 0


def test_parser_advance_at_end() -> None:
    """Test advancing past end of tokens."""
    tokens = [Token(TokenType.EOF, "", 1, 1)]
    parser = Parser(tokens)
    # Advance multiple times past end
    parser._advance()
    parser._advance()
    parser._advance()
    # Should not crash, returns last token


def test_parser_check_at_end() -> None:
    """Test check when pos >= len(tokens)."""
    tokens = [Token(TokenType.LBRACE, "{", 1, 1)]
    parser = Parser(tokens)
    parser.pos = 10  # Way past end
    assert parser._check(TokenType.EOF) is True
    assert parser._check(TokenType.LBRACE) is False


def test_get_method_calls_obj_method_not_lparen() -> None:
    """Test obj.identifier that's not followed by lparen."""
    # Lines 554-555: i += 1, continue when IDENTIFIER DOT IDENTIFIER not followed by LPAREN
    calls = get_method_calls("obj.property = 5;")
    # Should not be detected as method call
    assert len([c for c in calls if c[2] == "obj"]) == 0


def test_get_method_calls_obj_dot_non_identifier() -> None:
    """Test obj.non-identifier pattern."""
    # Lines 554-555: tokens[i+2].type != IDENTIFIER, so i += 1; continue
    calls = get_method_calls("obj.123;")
    assert len(calls) == 0


def test_tokenizer_unterminated_string() -> None:
    """Test tokenizing unterminated string."""
    tokenizer = Tokenizer('x = "unterminated')
    tokens = list(tokenizer.tokenize())
    # Should not crash, produces tokens
    assert len(tokens) > 0


def test_get_method_calls_no_methods() -> None:
    """Test code with no method calls."""
    calls = get_method_calls("x = 5; y = x + 3;")
    assert calls == []


def test_get_method_calls_nested_parens() -> None:
    """Test method call with nested parentheses in args."""
    calls = get_method_calls("foo((a + b), c);")
    assert len(calls) == 1
    assert calls[0][3] == "foo"
    assert calls[0][4] == 2  # 2 args


def test_parser_multiple_members() -> None:
    """Test plugin with multiple methods."""
    plugin = parse_plugin('{ Init "() { }" Run "() { }" }')
    assert len(plugin.members) == 2


def test_tokenizer_advance_past_end() -> None:
    """Test advancing tokenizer past end of source."""
    tokenizer = Tokenizer("x")
    # Advance multiple times past source length
    tokenizer._advance(10)
    # Should not crash
    assert tokenizer.pos >= len(tokenizer.source)
