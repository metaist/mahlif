"""Encoding utilities for text files.

Supports detection and conversion between encodings for both
plain text files and XML files.
"""

from __future__ import annotations

from pathlib import Path

# Canonical encoding names for CLI
ENCODINGS = {
    "utf8": "utf-8",
    "utf-8": "utf-8",
    "utf16": "utf-16",
    "utf-16": "utf-16",
    "utf16le": "utf-16-le",
    "utf-16-le": "utf-16-le",
    "utf16be": "utf-16-be",
    "utf-16-be": "utf-16-be",
    "latin1": "latin-1",
    "latin-1": "latin-1",
    "iso-8859-1": "latin-1",
    "ascii": "ascii",
}


def normalize_encoding(encoding: str) -> str:
    """Normalize encoding name to Python codec name.

    Args:
        encoding: Encoding name (e.g., 'utf8', 'utf-16-le')

    Returns:
        Normalized encoding name

    Raises:
        ValueError: If encoding is not recognized
    """
    key = encoding.lower().replace("_", "-")
    if key not in ENCODINGS:
        raise ValueError(f"Unknown encoding: {encoding}")
    return ENCODINGS[key]


def detect_encoding(path: str | Path) -> str:
    """Detect encoding of an XML file from BOM or declaration.

    Args:
        path: Path to XML file

    Returns:
        Encoding name (e.g., 'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be')
    """
    path = Path(path)
    with open(path, "rb") as f:
        # Read first 4 bytes for BOM detection
        bom = f.read(4)

    # Check for BOM (order matters - check longer BOMs first)
    if bom[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    # UTF-32 must be checked before UTF-16 since they share prefix bytes
    if bom[:4] == b"\x00\x00\xfe\xff":
        return "utf-32-be"
    if bom[:4] == b"\xff\xfe\x00\x00":
        return "utf-32-le"
    if bom[:2] == b"\xff\xfe":
        return "utf-16-le"
    if bom[:2] == b"\xfe\xff":
        return "utf-16-be"

    # No BOM - check XML declaration
    # Read enough for <?xml ... encoding="..." ?>
    with open(path, "rb") as f:
        header = f.read(200)

    # Handle UTF-16 without BOM (every other byte is 0)
    if b"\x00<\x00?" in header or b"<\x00?\x00" in header:
        if header[0:1] == b"\x00":
            return "utf-16-be"
        return "utf-16-le"

    # Check for encoding in XML declaration
    header_str = header.decode("ascii", errors="ignore")
    if 'encoding="UTF-16"' in header_str or "encoding='UTF-16'" in header_str:
        return "utf-16"
    if 'encoding="UTF-8"' in header_str or "encoding='UTF-8'" in header_str:
        return "utf-8"

    # Default to UTF-8
    return "utf-8"


def read_xml(path: str | Path) -> str:
    """Read XML file with automatic encoding detection.

    Args:
        path: Path to XML file

    Returns:
        XML content as string (BOM stripped if present)
    """
    path = Path(path)
    encoding = detect_encoding(path)
    with open(path, encoding=encoding) as f:
        content = f.read()

    # Strip BOM character if present
    if content and content[0] == "\ufeff":
        content = content[1:]

    return content


def read_xml_bytes(path: str | Path) -> bytes:
    """Read XML file as bytes for lxml parsing.

    lxml handles encoding automatically based on XML declaration/BOM.

    Args:
        path: Path to XML file

    Returns:
        Raw bytes for lxml to parse
    """
    path = Path(path)
    with open(path, "rb") as f:
        return f.read()


def convert_encoding(
    input_path: str | Path,
    target_encoding: str,
    output_path: str | Path | None = None,
    source_encoding: str | None = None,
) -> tuple[str, str, str]:
    """Convert a text file to a different encoding.

    Args:
        input_path: Path to input file
        target_encoding: Target encoding (e.g., 'utf-8', 'utf-16-le')
        output_path: Path to output file (default: overwrite input)
        source_encoding: Source encoding (default: auto-detect)

    Returns:
        Tuple of (output_path, source_encoding, target_encoding)
    """
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else input_path
    target_encoding = normalize_encoding(target_encoding)

    # Detect or normalize source encoding
    if source_encoding:
        source_encoding = normalize_encoding(source_encoding)
    else:
        source_encoding = detect_encoding(input_path)

    # Read content
    content = input_path.read_text(encoding=source_encoding)

    # Strip BOM if present
    if content and content[0] == "\ufeff":
        content = content[1:]

    # Update XML declaration if present
    if content.startswith("<?xml"):
        import re

        end_decl = content.find("?>")
        if end_decl != -1:
            decl = content[: end_decl + 2]
            rest = content[end_decl + 2 :]
            # Map encoding to XML-style name
            xml_encoding = target_encoding.upper().replace("-", "")
            match xml_encoding:
                case "UTF8":
                    xml_encoding = "UTF-8"
                case "UTF16" | "UTF16LE" | "UTF16BE":
                    xml_encoding = "UTF-16"  # XML doesn't distinguish LE/BE
                case _:  # pragma: no cover
                    pass  # Other encodings (e.g., LATIN1) keep original value
            new_decl = re.sub(
                r'encoding=["\'][^"\']*["\']',
                f'encoding="{xml_encoding}"',
                decl,
            )
            content = new_decl + rest

    # Write with target encoding
    output_path.write_text(content, encoding=target_encoding)

    return str(output_path), source_encoding, target_encoding


def convert_to_utf8(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> str:
    """Convert a file to UTF-8 encoding.

    Args:
        input_path: Path to input file (any encoding)
        output_path: Path to output file (default: overwrite input)

    Returns:
        Path to output file
    """
    result_path, _, _ = convert_encoding(input_path, "utf-8", output_path)
    return result_path


def encode_utf16be(content: str) -> bytes:
    """Encode string to UTF-16 BE with BOM.

    Args:
        content: Source content (string)

    Returns:
        UTF-16 BE encoded bytes with BOM prefix
    """
    return b"\xfe\xff" + content.encode("utf-16-be")


def encode_utf16le(content: str) -> bytes:
    """Encode string to UTF-16 LE with BOM.

    Args:
        content: Source content (string)

    Returns:
        UTF-16 LE encoded bytes with BOM prefix
    """
    return b"\xff\xfe" + content.encode("utf-16-le")
