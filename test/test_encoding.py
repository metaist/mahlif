"""Tests for encoding detection and conversion."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mahlif import convert_to_utf8
from mahlif import detect_encoding
from mahlif import parse
from mahlif import read_xml
from mahlif.encoding import read_xml_bytes


class TestDetectEncoding:
    """Test encoding detection."""

    def test_utf8(self) -> None:
        """Detect UTF-8 encoding."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<mahlif/>')
            path = f.name
        try:
            enc = detect_encoding(path)
            assert enc == "utf-8"
        finally:
            Path(path).unlink()

    def test_utf8_single_quotes(self) -> None:
        """Detect UTF-8 encoding with single quotes."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            f.write(b"<?xml version='1.0' encoding='UTF-8'?>\n<mahlif/>")
            path = f.name
        try:
            enc = detect_encoding(path)
            assert enc == "utf-8"
        finally:
            Path(path).unlink()

    def test_utf8_bom(self) -> None:
        """Detect UTF-8 with BOM."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            f.write(b"\xef\xbb\xbf<?xml version='1.0'?>\n<mahlif/>")
            path = f.name
        try:
            enc = detect_encoding(path)
            assert enc == "utf-8-sig"
        finally:
            Path(path).unlink()

    def test_utf16_be_bom(self) -> None:
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

    def test_utf16_le_bom(self) -> None:
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

    def test_utf32_be_bom(self) -> None:
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

    def test_utf32_le_bom(self) -> None:
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

    def test_utf16_no_bom_be(self) -> None:
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

    def test_utf16_no_bom_le(self) -> None:
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

    def test_utf16_from_declaration(self) -> None:
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

    def test_default_utf8(self) -> None:
        """Default to UTF-8 when no encoding info."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            f.write(b"<mahlif/>")
            path = f.name
        try:
            enc = detect_encoding(path)
            assert enc == "utf-8"
        finally:
            Path(path).unlink()


class TestReadXml:
    """Test XML file reading."""

    def test_utf8(self) -> None:
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

    def test_utf16_be(self) -> None:
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

    def test_no_bom(self) -> None:
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

    def test_bytes(self) -> None:
        """Read XML as raw bytes."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            f.write(b"<mahlif/>")
            path = f.name
        try:
            content = read_xml_bytes(path)
            assert content == b"<mahlif/>"
        finally:
            Path(path).unlink()


class TestConvertToUtf8:
    """Test UTF-8 conversion."""

    def test_utf16_to_utf8(self) -> None:
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

    def test_inplace(self) -> None:
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

    def test_no_xml_declaration(self) -> None:
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

    def test_declaration_no_end(self) -> None:
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


class TestParseUtf16:
    """Test parsing UTF-16 files."""

    def test_parse_utf16_file(self) -> None:
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
