"""Tests for mahlif package."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mahlif import convert_to_utf8, detect_encoding, parse, read_xml, to_lilypond
from mahlif.models import Note, NoteRest, Position, Score


class TestModels:
    """Test data models."""

    def test_noterest_is_rest(self) -> None:
        """A NoteRest with no notes is a rest."""
        nr = NoteRest(pos=0, dur=256)
        assert nr.is_rest is True
        assert nr.is_chord is False

    def test_noterest_single_note(self) -> None:
        """A NoteRest with one note is not a chord."""
        nr = NoteRest(pos=0, dur=256, notes=[Note(pitch=60)])
        assert nr.is_rest is False
        assert nr.is_chord is False

    def test_noterest_chord(self) -> None:
        """A NoteRest with multiple notes is a chord."""
        nr = NoteRest(
            pos=0,
            dur=256,
            notes=[Note(pitch=60), Note(pitch=64), Note(pitch=67)],
        )
        assert nr.is_rest is False
        assert nr.is_chord is True

    def test_score_single_movement(self) -> None:
        """A score with no movements is single-movement."""
        score = Score()
        assert score.is_multi_movement is False

    def test_position_defaults(self) -> None:
        """Position defaults to zero offsets."""
        pos = Position()
        assert pos.dx == 0.0
        assert pos.dy == 0.0


class TestParser:
    """Test XML parser."""

    def test_parse_empty_score(self) -> None:
        """Parse minimal valid Mahlif XML."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <meta>
                <work-title>Test Score</work-title>
            </meta>
        </mahlif>
        """
        score = parse(xml)
        assert score.meta.work_title == "Test Score"
        assert score.is_multi_movement is False

    def test_parse_single_note(self) -> None:
        """Parse a score with a single note."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1" instrument="Piano" clef="treble">
                    <bar n="1" length="1024">
                        <note pos="0" dur="256" voice="1" pitch="60" accidental=""/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        assert len(score.staves) == 1
        assert len(score.staves[0].bars) == 1
        assert len(score.staves[0].bars[0].elements) == 1

        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, NoteRest)
        assert len(elem.notes) == 1
        assert elem.notes[0].pitch == 60

    def test_parse_chord(self) -> None:
        """Parse a chord."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <chord pos="0" dur="256" voice="1">
                            <n p="60" d="0" a=""/>
                            <n p="64" d="2" a=""/>
                            <n p="67" d="4" a=""/>
                        </chord>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, NoteRest)
        assert elem.is_chord is True
        assert len(elem.notes) == 3

    def test_parse_rest(self) -> None:
        """Parse a rest."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <rest pos="0" dur="256" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, NoteRest)
        assert elem.is_rest is True


class TestLilypond:
    """Test LilyPond conversion."""

    def test_empty_score(self) -> None:
        """Convert empty score to LilyPond."""
        score = Score()
        lily = to_lilypond(score)
        assert '\\version "2.24.0"' in lily
        assert "\\header" in lily

    def test_score_with_metadata(self) -> None:
        """Convert score with metadata."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <meta>
                <work-title>Test Title</work-title>
                <composer>Test Composer</composer>
            </meta>
        </mahlif>
        """
        score = parse(xml)
        lily = to_lilypond(score)
        assert 'title = "Test Title"' in lily
        assert 'composer = "Test Composer"' in lily

    def test_single_note_conversion(self) -> None:
        """Convert a single note."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1" instrument="Piano" clef="treble">
                    <bar n="1" length="1024">
                        <note pos="0" dur="256" voice="1" pitch="60" accidental=""/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        lily = to_lilypond(score)
        # c' = middle C (MIDI 60), 4 = quarter note
        assert "c'4" in lily

    def test_chord_conversion(self) -> None:
        """Convert a C major chord."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <chord pos="0" dur="256" voice="1">
                            <n p="60" d="0" a=""/>
                            <n p="64" d="2" a=""/>
                            <n p="67" d="4" a=""/>
                        </chord>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        lily = to_lilypond(score)
        # Should produce <c' e' g'>4
        assert "<c' e' g'>4" in lily

    def test_rest_conversion(self) -> None:
        """Convert a quarter rest."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <rest pos="0" dur="256" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        lily = to_lilypond(score)
        assert "r4" in lily

    def test_hidden_rest_is_spacer(self) -> None:
        """Hidden rest becomes spacer rest."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <rest pos="0" dur="256" voice="1" hidden="true"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        lily = to_lilypond(score)
        assert "s4" in lily


class TestEncoding:
    """Test encoding detection and conversion."""

    def test_detect_utf8(self) -> None:
        """Detect UTF-8 encoding."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<mahlif/>')
            path = f.name
        try:
            enc = detect_encoding(path)
            assert enc == "utf-8"
        finally:
            Path(path).unlink()

    def test_detect_utf16_be_bom(self) -> None:
        """Detect UTF-16 BE from BOM."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            # UTF-16 BE BOM + content
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

    def test_detect_utf16_le_bom(self) -> None:
        """Detect UTF-16 LE from BOM."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            # UTF-16 LE BOM + content
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

    def test_read_utf8(self) -> None:
        """Read UTF-8 file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n<mahlif><text>Привет</text></mahlif>'
            )
            path = f.name
        try:
            content = read_xml(path)
            assert "Привет" in content
        finally:
            Path(path).unlink()

    def test_read_utf16_be(self) -> None:
        """Read UTF-16 BE file with BOM."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            content = '<?xml version="1.0" encoding="UTF-16"?>\n<mahlif><text>Привет</text></mahlif>'
            f.write(b"\xfe\xff")
            f.write(content.encode("utf-16-be"))
            path = f.name
        try:
            result = read_xml(path)
            assert "Привет" in result
        finally:
            Path(path).unlink()

    def test_convert_utf16_to_utf8(self) -> None:
        """Convert UTF-16 file to UTF-8."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as f:
            content = '<?xml version="1.0" encoding="UTF-16"?>\n<mahlif><text>Привет мир</text></mahlif>'
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
