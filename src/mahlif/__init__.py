"""Universal music notation interchange format with bidirectional converters."""

__version__ = "0.1.0"
__pubdate__ = "2026-01-30T20:37:40Z"

from mahlif.encoding import convert_to_utf8
from mahlif.encoding import detect_encoding
from mahlif.encoding import read_xml
from mahlif.lilypond import to_lilypond
from mahlif.parser import parse

__all__ = ["convert_to_utf8", "detect_encoding", "parse", "read_xml", "to_lilypond"]
