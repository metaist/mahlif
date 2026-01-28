"""Universal music notation interchange format with bidirectional converters."""

__version__ = "0.1.0"
__pubdate__ = "unpublished"

from mahlif.parser import parse
from mahlif.lilypond import to_lilypond
from mahlif.encoding import convert_to_utf8, detect_encoding, read_xml

__all__ = ["parse", "to_lilypond", "convert_to_utf8", "detect_encoding", "read_xml"]
