"""Tests for mahlif XML parser."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mahlif import parse
from mahlif.models import Barline
from mahlif.models import Clef
from mahlif.models import Dynamic
from mahlif.models import Grace
from mahlif.models import Hairpin
from mahlif.models import KeySignature
from mahlif.models import NoteRest
from mahlif.models import Octava
from mahlif.models import Pedal
from mahlif.models import Slur
from mahlif.models import Text
from mahlif.models import TimeSignature
from mahlif.models import Trill
from mahlif.models import Tuplet


class TestParseBasic:
    """Test basic parsing functionality."""

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

    def test_parse_bytes(self) -> None:
        """Parse from raw bytes."""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <meta><work-title>Bytes Test</work-title></meta>
        </mahlif>
        """
        score = parse(xml)
        assert score.meta.work_title == "Bytes Test"

    def test_parse_path(self) -> None:
        """Parse from file path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                "<mahlif><meta><work-title>Path Test</work-title></meta></mahlif>"
            )
            path = f.name
        try:
            score = parse(path)
            assert score.meta.work_title == "Path Test"

            # Also test with Path object
            score2 = parse(Path(path))
            assert score2.meta.work_title == "Path Test"
        finally:
            Path(path).unlink()


class TestParseNotes:
    """Test parsing notes, chords, and rests."""

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

    def test_parse_articulations(self) -> None:
        """Parse note with articulations."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <note pos="0" dur="256" pitch="60" articulations="staccato accent"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, NoteRest)
        assert elem.articulations == ["staccato", "accent"]

    def test_parse_tied_note(self) -> None:
        """Parse tied note."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <note pos="0" dur="256" pitch="60" tied="true"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, NoteRest)
        assert elem.notes[0].tied is True

    def test_parse_stem_beam(self) -> None:
        """Parse stem and beam attributes."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <note pos="0" dur="128" pitch="60" stem="up" beam="start"/>
                        <note pos="128" dur="128" pitch="62" stem="down" beam="end"/>
                        <note pos="256" dur="128" pitch="64" stem="invalid" beam="invalid"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem1 = score.staves[0].bars[0].elements[0]
        elem2 = score.staves[0].bars[0].elements[1]
        elem3 = score.staves[0].bars[0].elements[2]
        assert isinstance(elem1, NoteRest)
        assert elem1.stem == "up"
        assert elem1.beam == "start"
        assert isinstance(elem2, NoteRest)
        assert elem2.stem == "down"
        assert elem2.beam == "end"
        # Invalid values should default to "auto"
        assert isinstance(elem3, NoteRest)
        assert elem3.stem == "auto"
        assert elem3.beam == "auto"

    def test_parse_written_pitch(self) -> None:
        """Parse note with written pitch (transposing instruments)."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <note pos="0" dur="256" pitch="60" written-pitch="62"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, NoteRest)
        assert elem.notes[0].pitch == 60
        assert elem.notes[0].written_pitch == 62


class TestParseNotation:
    """Test parsing notation elements."""

    def test_parse_clef(self) -> None:
        """Parse clef changes."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <clef pos="0" type="bass" dx="5" dy="10"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Clef)
        assert elem.type == "bass"
        assert elem.offset.dx == 5.0
        assert elem.offset.dy == 10.0

    def test_parse_key_signature(self) -> None:
        """Parse key signature."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <key pos="0" fifths="-3" mode="minor"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, KeySignature)
        assert elem.fifths == -3
        assert elem.mode == "minor"

    def test_parse_key_signature_invalid_mode(self) -> None:
        """Parse key signature with invalid mode defaults to major."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <key pos="0" fifths="2" mode="invalid"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, KeySignature)
        assert elem.mode == "major"

    def test_parse_time_signature(self) -> None:
        """Parse time signature."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <time pos="0" num="3" den="4"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, TimeSignature)
        assert elem.num == 3
        assert elem.den == 4

    def test_parse_barline(self) -> None:
        """Parse special barline."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <barline pos="1024" type="double"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Barline)
        assert elem.type == "double"

    def test_parse_barline_with_following_element(self) -> None:
        """Parse barline followed by another element (tests loop continuation)."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <barline pos="0" type="repeat-start"/>
                        <note pos="0" dur="256" pitch="60"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        assert len(score.staves[0].bars[0].elements) == 2
        assert isinstance(score.staves[0].bars[0].elements[0], Barline)
        assert isinstance(score.staves[0].bars[0].elements[1], NoteRest)

    def test_parse_bar_break(self) -> None:
        """Parse bar with break attribute."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024" break="page"/>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        assert score.staves[0].bars[0].break_type == "page"


class TestParseExpressions:
    """Test parsing dynamics, text, and other expressions."""

    def test_parse_dynamic(self) -> None:
        """Parse dynamic marking."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <dynamic pos="0" text="ff" voice="1" dx="5" dy="-10"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Dynamic)
        assert elem.text == "ff"
        assert elem.voice == 1
        assert elem.offset.dx == 5.0
        assert elem.offset.dy == -10.0

    def test_parse_text(self) -> None:
        """Parse text annotation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <text pos="0" style="technique" voice="1">pizz.</text>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Text)
        assert elem.text == "pizz."
        assert elem.style == "technique"


class TestParseSpanners:
    """Test parsing slurs, hairpins, and other spanners."""

    def test_parse_slur(self) -> None:
        """Parse slur."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <slur start-bar="1" start-pos="0" end-bar="1" end-pos="512" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Slur)
        assert elem.start_bar == 1
        assert elem.end_pos == 512

    def test_parse_hairpin(self) -> None:
        """Parse hairpin (crescendo/diminuendo)."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <hairpin type="cresc" start-bar="1" start-pos="0" end-bar="2" end-pos="256" voice="1"/>
                        <hairpin type="dim" start-bar="1" start-pos="512" end-bar="1" end-pos="1024" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem1 = score.staves[0].bars[0].elements[0]
        elem2 = score.staves[0].bars[0].elements[1]
        assert isinstance(elem1, Hairpin)
        assert elem1.type == "cresc"
        assert isinstance(elem2, Hairpin)
        assert elem2.type == "dim"

    def test_parse_hairpin_invalid_type(self) -> None:
        """Parse hairpin with invalid type defaults to cresc."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <hairpin type="invalid" start-bar="1" start-pos="0" end-bar="1" end-pos="512" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Hairpin)
        assert elem.type == "cresc"

    def test_parse_tuplet(self) -> None:
        """Parse tuplet."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <tuplet start-bar="1" start-pos="0" num="3" den="2"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Tuplet)
        assert elem.num == 3
        assert elem.den == 2


class TestParseLyrics:
    """Test parsing lyrics."""

    def test_parse_lyrics(self) -> None:
        """Parse lyrics."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024"/>
                    <lyrics voice="1" verse="1">
                        <syl pos="0" bar="1">Hel</syl>
                        <syl pos="256" bar="1" hyphen="true">lo</syl>
                        <syl pos="512" melisma="true">world</syl>
                    </lyrics>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        assert len(score.staves[0].lyrics) == 1
        lyrics = score.staves[0].lyrics[0]
        assert lyrics.verse == 1
        assert len(lyrics.syllables) == 3
        assert lyrics.syllables[0].text == "Hel"
        assert lyrics.syllables[1].hyphen is True
        assert lyrics.syllables[2].melisma is True


class TestParseStructure:
    """Test parsing score structure (meta, layout, movements)."""

    def test_parse_layout(self) -> None:
        """Parse layout."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <layout>
                <page width="300" height="400" unit="mm"/>
                <staff-height>8.5</staff-height>
            </layout>
        </mahlif>
        """
        score = parse(xml)
        assert score.layout.page_width == 300.0
        assert score.layout.page_height == 400.0
        assert score.layout.staff_height == 8.5

    def test_parse_full_meta(self) -> None:
        """Parse complete metadata."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <meta>
                <work-title>Symphony No. 5</work-title>
                <composer>Beethoven</composer>
                <lyricist>N/A</lyricist>
                <arranger>None</arranger>
                <copyright>Public Domain</copyright>
                <publisher>Test Publisher</publisher>
                <source-file>/path/to/file.sib</source-file>
                <source-format>Sibelius 2024</source-format>
                <duration-ms>180000</duration-ms>
            </meta>
        </mahlif>
        """
        score = parse(xml)
        assert score.meta.work_title == "Symphony No. 5"
        assert score.meta.composer == "Beethoven"
        assert score.meta.lyricist == "N/A"
        assert score.meta.arranger == "None"
        assert score.meta.copyright == "Public Domain"
        assert score.meta.publisher == "Test Publisher"
        assert score.meta.source_file == "/path/to/file.sib"
        assert score.meta.source_format == "Sibelius 2024"
        assert score.meta.duration_ms == 180000

    def test_parse_system_staff(self) -> None:
        """Parse system staff."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <system-staff>
                <bar n="1">
                    <time pos="0" num="4" den="4"/>
                </bar>
            </system-staff>
        </mahlif>
        """
        score = parse(xml)
        assert len(score.system_staff.bars) == 1
        elem = score.system_staff.bars[0].elements[0]
        assert isinstance(elem, TimeSignature)

    def test_parse_multi_movement(self) -> None:
        """Parse multi-movement score."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <meta><work-title>Sonata</work-title></meta>
            <movements>
                <movement n="1">
                    <movement-meta><title>Allegro</title></movement-meta>
                    <layout>
                        <page width="210" height="297"/>
                        <staff-height>7</staff-height>
                    </layout>
                    <staves count="1">
                        <staff n="1" instrument="Piano">
                            <bar n="1" length="1024"/>
                        </staff>
                    </staves>
                    <system-staff>
                        <bar n="1"/>
                    </system-staff>
                </movement>
                <movement n="2">
                    <movement-meta><title>Adagio</title></movement-meta>
                </movement>
            </movements>
        </mahlif>
        """
        score = parse(xml)
        assert score.is_multi_movement is True
        assert len(score.movements) == 2
        assert score.movements[0].title == "Allegro"
        assert score.movements[1].title == "Adagio"
        assert len(score.movements[0].staves) == 1
        assert score.movements[0].staves[0].instrument == "Piano"

    def test_parse_tempo_and_rehearsal_ignored(self) -> None:
        """Tempo and rehearsal in bars are ignored (handled at system level)."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <tempo pos="0" text="Allegro"/>
                        <rehearsal pos="0">A</rehearsal>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        # These elements are skipped in bar parsing
        assert len(score.staves[0].bars[0].elements) == 0

    def test_parse_octava(self) -> None:
        """Parse octava (8va/8vb) lines."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <octava type="8va" start-bar="1" start-pos="0"
                                end-bar="2" end-pos="512" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Octava)
        assert elem.type == "8va"
        assert elem.start_bar == 1
        assert elem.end_bar == 2

    def test_parse_pedal(self) -> None:
        """Parse pedal lines."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <pedal type="sustain" start-bar="1" start-pos="0"
                               end-bar="1" end-pos="1024"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Pedal)
        assert elem.type == "sustain"

    def test_parse_trill(self) -> None:
        """Parse trill lines."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <trill start-bar="1" start-pos="256"
                               end-bar="1" end-pos="768" voice="1"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Trill)
        assert elem.start_pos == 256
        assert elem.end_pos == 768

    def test_parse_grace(self) -> None:
        """Parse grace notes."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1">
                    <bar n="1" length="1024">
                        <grace pos="256" type="acciaccatura" pitch="67" dur="64"/>
                    </bar>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        elem = score.staves[0].bars[0].elements[0]
        assert isinstance(elem, Grace)
        assert elem.type == "acciaccatura"
        assert elem.pitch == 67

    def test_parse_staff_attributes(self) -> None:
        """Parse extended staff attributes."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <mahlif version="1.0">
            <staves count="1">
                <staff n="1" instrument="Violin I"
                       full-name="Violin I" short-name="Vn. I"
                       size="75" lines="5">
                    <bar n="1" length="1024"/>
                </staff>
            </staves>
        </mahlif>
        """
        score = parse(xml)
        staff = score.staves[0]
        assert staff.full_name == "Violin I"
        assert staff.short_name == "Vn. I"
        assert staff.size == 75
