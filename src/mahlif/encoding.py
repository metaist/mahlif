"""Encoding utilities for Mahlif XML files."""

from __future__ import annotations

from pathlib import Path


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

    # Check for BOM
    if bom[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    if bom[:2] == b"\xff\xfe":
        return "utf-16-le"
    if bom[:2] == b"\xfe\xff":
        return "utf-16-be"
    if bom[:4] == b"\x00\x00\xfe\xff":
        return "utf-32-be"
    if bom[:4] == b"\xff\xfe\x00\x00":
        return "utf-32-le"

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


def convert_to_utf8(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> str:
    """Convert a Mahlif XML file to UTF-8 encoding.

    Args:
        input_path: Path to input XML file (any encoding)
        output_path: Path to output file (default: overwrite input)

    Returns:
        Path to output file
    """
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else input_path

    # Read with auto-detected encoding
    content = read_xml(input_path)

    # Update XML declaration to UTF-8
    if content.startswith("<?xml"):
        # Replace encoding in declaration
        end_decl = content.find("?>")
        if end_decl != -1:
            decl = content[: end_decl + 2]
            rest = content[end_decl + 2 :]

            # Replace encoding attribute
            import re

            new_decl = re.sub(
                r'encoding=["\'][^"\']*["\']',
                'encoding="UTF-8"',
                decl,
            )
            content = new_decl + rest

    # Write as UTF-8
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(output_path)
