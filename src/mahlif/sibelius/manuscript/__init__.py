"""ManuScript language support for Sibelius plugins.

This package provides parsing, AST representation, and checking for ManuScript,
the scripting language used in Sibelius plugins (.plg files).
"""

from .ast import parse_plugin as parse
from .ast import Plugin
from .checker import check_method_body
from .checker import MethodBodyChecker
from .errors import CheckError
from .tokenizer import MethodBodyTokenizer
from .tokenizer import Token
from .tokenizer import TokenType

__all__ = [
    # AST
    "parse",
    "Plugin",
    # Checker
    "check_method_body",
    "MethodBodyChecker",
    # Tokenizer
    "MethodBodyTokenizer",
    "Token",
    "TokenType",
    # Errors
    "CheckError",
]
