"""Tests for encoding detection and conversion."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mahlif import convert_to_utf8
from mahlif import detect_encoding
from mahlif import parse
from mahlif import read_xml
from mahlif.encoding import read_xml_bytes


# ----------------------------------------------------------------------
# TestDetectEncoding: Test encoding detection.
# ----------------------------------------------------------------------


def test_detect_utf8() -> None:
    """Detect UTF-8 encoding."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<mahlif/>')
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-8"
    finally:
        Path(path).unlink()


def test_utf8_single_quotes() -> None:
    """Detect UTF-8 encoding with single quotes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"<?xml version='1.0' encoding='UTF-8'?>\n<mahlif/>")
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-8"
    finally:
        Path(path).unlink()


def test_utf8_bom() -> None:
    """Detect UTF-8 with BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"\xef\xbb\xbf<?xml version='1.0'?>\n<mahlif/>")
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-8-sig"
    finally:
        Path(path).unlink()


def test_utf16_be_bom() -> None:
    """Detect UTF-16 BE from BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"\xfe\xff")
        f.write(
            '<?xml version="1.0" encoding="UTF-16"?>\n<mahlif/>'.encode("utf-16-be")
        )
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-16-be"
    finally:
        Path(path).unlink()


def test_utf16_le_bom() -> None:
    """Detect UTF-16 LE from BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"\xff\xfe")
        f.write(
            '<?xml version="1.0" encoding="UTF-16"?>\n<mahlif/>'.encode("utf-16-le")
        )
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-16-le"
    finally:
        Path(path).unlink()


def test_utf32_be_bom() -> None:
    """Detect UTF-32 BE from BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"\x00\x00\xfe\xff")
        f.write(b"<mahlif/>")  # Simplified
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-32-be"
    finally:
        Path(path).unlink()


def test_utf32_le_bom() -> None:
    """Detect UTF-32 LE from BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"\xff\xfe\x00\x00")
        f.write(b"<mahlif/>")  # Simplified
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-32-le"
    finally:
        Path(path).unlink()


def test_utf16_no_bom_be() -> None:
    """Detect UTF-16 BE without BOM from null bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        # UTF-16 BE without BOM - starts with \x00<
        content = '<?xml version="1.0"?><mahlif/>'
        f.write(content.encode("utf-16-be"))
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-16-be"
    finally:
        Path(path).unlink()


def test_utf16_no_bom_le() -> None:
    """Detect UTF-16 LE without BOM from null bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        # UTF-16 LE without BOM - has <\x00
        content = '<?xml version="1.0"?><mahlif/>'
        f.write(content.encode("utf-16-le"))
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-16-le"
    finally:
        Path(path).unlink()


def test_utf16_from_declaration() -> None:
    """Detect UTF-16 from XML declaration (edge case)."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        # This is technically invalid but tests the declaration parsing
        f.write(b'<?xml version="1.0" encoding="UTF-16"?>\n<mahlif/>')
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-16"
    finally:
        Path(path).unlink()


def test_default_utf8() -> None:
    """Default to UTF-8 when no encoding info."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"<mahlif/>")
        path = f.name
    try:
        enc = detect_encoding(path)
        assert enc == "utf-8"
    finally:
        Path(path).unlink()


# ----------------------------------------------------------------------
# TestReadXml: Test XML file reading.
# ----------------------------------------------------------------------


def test_read_utf8() -> None:
    """Read UTF-8 file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<mahlif><text>Привет</text></mahlif>"
        )
        path = f.name
    try:
        content = read_xml(path)
        assert "Привет" in content
    finally:
        Path(path).unlink()


def test_utf16_be() -> None:
    """Read UTF-16 BE file with BOM."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        content = (
            '<?xml version="1.0" encoding="UTF-16"?>\n'
            "<mahlif><text>Привет</text></mahlif>"
        )
        f.write(b"\xfe\xff")
        f.write(content.encode("utf-16-be"))
        path = f.name
    try:
        result = read_xml(path)
        assert "Привет" in result
        # BOM should be stripped
        assert result[0] != "\ufeff"
    finally:
        Path(path).unlink()


def test_no_bom() -> None:
    """Read file without BOM character."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    ) as f:
        f.write("<mahlif/>")
        path = f.name
    try:
        content = read_xml(path)
        assert content == "<mahlif/>"
    finally:
        Path(path).unlink()


def test_bytes() -> None:
    """Read XML as raw bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        f.write(b"<mahlif/>")
        path = f.name
    try:
        content = read_xml_bytes(path)
        assert content == b"<mahlif/>"
    finally:
        Path(path).unlink()


# ----------------------------------------------------------------------
# TestConvertToUtf8: Test UTF-8 conversion.
# ----------------------------------------------------------------------


def test_utf16_to_utf8() -> None:
    """Convert UTF-16 file to UTF-8."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        content = (
            '<?xml version="1.0" encoding="UTF-16"?>\n'
            "<mahlif><text>Привет мир</text></mahlif>"
        )
        f.write(b"\xfe\xff")
        f.write(content.encode("utf-16-be"))
        input_path = f.name

    output_path = input_path + ".utf8.xml"
    try:
        convert_to_utf8(input_path, output_path)

        # Verify output is UTF-8
        with open(output_path, "rb") as f:
            raw = f.read()
        assert b"\xfe\xff" not in raw  # No BOM
        assert b'encoding="UTF-8"' in raw

        # Verify content preserved
        with open(output_path, encoding="utf-8") as f:
            result = f.read()
        assert "Привет мир" in result
    finally:
        Path(input_path).unlink()
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_inplace() -> None:
    """Convert file in place (no output path)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    ) as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<mahlif>test</mahlif>')
        path = f.name
    try:
        result_path = convert_to_utf8(path)
        assert result_path == path

        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "test" in content
    finally:
        Path(path).unlink()


def test_no_xml_declaration() -> None:
    """Convert file without XML declaration."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    ) as f:
        f.write("<mahlif>no declaration</mahlif>")
        path = f.name

    output_path = path + ".out.xml"
    try:
        convert_to_utf8(path, output_path)

        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        # Content preserved, no encoding added since no declaration
        assert "no declaration" in content
    finally:
        Path(path).unlink()
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_declaration_no_end() -> None:
    """Convert file with malformed declaration (no ?>)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-8"
    ) as f:
        f.write('<?xml version="1.0" encoding="UTF-8"<mahlif/>')
        path = f.name

    output_path = path + ".out.xml"
    try:
        convert_to_utf8(path, output_path)

        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        # Should preserve content even with malformed declaration
        assert "<mahlif/>" in content
    finally:
        Path(path).unlink()
        if Path(output_path).exists():
            Path(output_path).unlink()


# ----------------------------------------------------------------------
# TestParseUtf16: Test parsing UTF-16 files.
# ----------------------------------------------------------------------


def test_parse_utf16_file() -> None:
    """Parse UTF-16 encoded Mahlif file."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
        content = """<?xml version="1.0" encoding="UTF-16"?>
<mahlif version="1.0">
<meta>
        <work-title>Тестовая партитура</work-title>
        <composer>Чайковский</composer>
</meta>
</mahlif>"""
        f.write(b"\xfe\xff")
        f.write(content.encode("utf-16-be"))
        path = f.name
    try:
        score = parse(path)
        assert score.meta.work_title == "Тестовая партитура"
        assert score.meta.composer == "Чайковский"
    finally:
        Path(path).unlink()


def test_normalize_unknown_encoding() -> None:
    """Test normalize_encoding raises for unknown encoding."""
    from mahlif.encoding import normalize_encoding
    import pytest

    with pytest.raises(ValueError, match="Unknown encoding"):
        normalize_encoding("invalid-xyz")


def test_convert_with_source_encoding(tmp_path: Path) -> None:
    """Test convert_encoding with explicit source encoding."""
    from mahlif.encoding import convert_encoding

    src = tmp_path / "test.txt"
    src.write_text("Hello", encoding="utf-8")

    result_path, src_enc, dest_enc = convert_encoding(
        src, "utf-16", source_encoding="utf-8"
    )
    assert src_enc == "utf-8"


def test_convert_xml_utf16(tmp_path: Path) -> None:
    """Test convert_encoding updates XML declaration for UTF-16."""
    from mahlif.encoding import convert_encoding

    src = tmp_path / "test.xml"
    src.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<root/>', encoding="utf-8")
    dest = tmp_path / "test_utf16.xml"

    convert_encoding(src, "utf-16", dest)
    content = dest.read_text(encoding="utf-16")
    assert "UTF-16" in content


def test_convert_xml_utf16le(tmp_path: Path) -> None:
    """Test convert_encoding updates XML declaration for UTF-16LE."""
    from mahlif.encoding import convert_encoding

    src = tmp_path / "test.xml"
    src.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<root/>', encoding="utf-8")
    dest = tmp_path / "test_utf16le.xml"

    convert_encoding(src, "utf-16-le", dest)
    content = dest.read_text(encoding="utf-16-le")
    assert "UTF-16" in content


def test_convert_xml_utf16be(tmp_path: Path) -> None:
    """Test convert_encoding updates XML declaration for UTF-16BE."""
    from mahlif.encoding import convert_encoding

    src = tmp_path / "test.xml"
    src.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<root/>', encoding="utf-8")
    dest = tmp_path / "test_utf16be.xml"

    convert_encoding(src, "utf-16-be", dest)
    content = dest.read_text(encoding="utf-16-be")
    assert "UTF-16" in content


def test_encode_utf16le() -> None:
    """Test encode_utf16le adds BOM prefix."""
    from mahlif.encoding import encode_utf16le

    result = encode_utf16le("Hello")
    assert result.startswith(b"\xff\xfe")
