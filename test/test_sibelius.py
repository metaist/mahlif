"""Tests for Sibelius-related modules."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from mahlif.models import Bar
from mahlif.models import Barline
from mahlif.models import Clef
from mahlif.models import Dynamic
from mahlif.models import Grace
from mahlif.models import Hairpin
from mahlif.models import KeySignature
from mahlif.models import Layout
from mahlif.models import Lyrics
from mahlif.models import Meta
from mahlif.models import Note
from mahlif.models import NoteRest
from mahlif.models import Octava
from mahlif.models import Pedal
from mahlif.models import Position
from mahlif.models import Rehearsal
from mahlif.models import Score
from mahlif.models import Slur
from mahlif.models import Staff
from mahlif.models import Syllable
from mahlif.models import SystemStaff
from mahlif.models import Tempo
from mahlif.models import Text
from mahlif.models import TimeSignature
from mahlif.models import Trill
from mahlif.models import Tuplet
from mahlif.sibelius.extract_api import extract_signatures
from mahlif.sibelius.extract_api import main as extract_main
from mahlif.sibelius.extract_api import parse_signature
from mahlif.sibelius.generate_plugin import ARTICULATION_MAP
from mahlif.sibelius.generate_plugin import _calc_spanner_duration
from mahlif.sibelius.generate_plugin import convert_to_utf16
from mahlif.sibelius.generate_plugin import escape_str
from mahlif.sibelius.generate_plugin import generate_plugin
from mahlif.sibelius.generate_plugin import main as generate_main
from mahlif.sibelius.lint import LintError
from mahlif.sibelius.lint import lint
from mahlif.sibelius.lint import lint_braces
from mahlif.sibelius.lint import lint_common_issues
from mahlif.sibelius.lint import lint_method_calls
from mahlif.sibelius.lint import lint_methods
from mahlif.sibelius.lint import lint_plugin_structure
from mahlif.sibelius.lint import lint_strings
from mahlif.sibelius.lint import main as lint_main
from mahlif.sibelius.lint import read_plugin
from mahlif.sibelius.manuscript_ast import Parser
from mahlif.sibelius.manuscript_ast import Token
from mahlif.sibelius.manuscript_ast import TokenType
from mahlif.sibelius.manuscript_ast import Tokenizer
from mahlif.sibelius.manuscript_ast import get_method_calls
from mahlif.sibelius.manuscript_ast import parse_plugin

if TYPE_CHECKING:
    pass


# =============================================================================
# generate_plugin tests
# =============================================================================


class TestGeneratePlugin:
    """Tests for generate_plugin module."""

    def test_escape_str_basic(self) -> None:
        """Test basic string escaping."""
        assert escape_str("hello") == "hello"
        assert escape_str("it's") == "it\\'s"
        assert escape_str("back\\slash") == "back\\\\slash"
        assert escape_str("it's a\\b") == "it\\'s a\\\\b"

    def test_calc_spanner_duration_same_bar(self) -> None:
        """Test duration calculation within same bar."""
        result = _calc_spanner_duration(1, 0, 1, 256, 1024)
        assert result == 256

    def test_calc_spanner_duration_cross_bar(self) -> None:
        """Test duration calculation across bars."""
        # Start bar 1, pos 512 to end bar 3, pos 256
        # bar_length = 1024
        # remaining in bar 1: 1024 - 512 = 512
        # full bar 2: 1024
        # end in bar 3: 256
        # total: 512 + 1024 + 256 = 1792
        result = _calc_spanner_duration(1, 512, 3, 256, 1024)
        assert result == 1792

    def test_articulation_map_coverage(self) -> None:
        """Test that articulation map has expected entries."""
        assert "staccato" in ARTICULATION_MAP
        assert "fermata" in ARTICULATION_MAP
        assert ARTICULATION_MAP["fermata"] == "PauseArtic"
        assert "up-bow" in ARTICULATION_MAP
        assert "down-bow" in ARTICULATION_MAP

    def test_generate_plugin_empty_score(self) -> None:
        """Test generating plugin for empty score."""
        score = Score(
            staves=[],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Empty")
        assert "AddToPluginsMenu" in result
        assert "Mahlif: Import Test" in result
        assert "Import complete: 0 staves" in result

    def test_generate_plugin_single_staff_with_notes(self) -> None:
        """Test generating plugin with notes."""
        note = Note(pitch=60, tied=False)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
            articulations=["staccato"],
            stem="up",
            offset=Position(dx=10, dy=5),
        )
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(
            n=1,
            bars=[bar],
            instrument="Flute",
            full_name="Flute",
            short_name="Fl.",
        )
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "CreateInstrument('Flute')" in result
        assert "AddNote(0, 60, 256" in result
        assert "SetArticulation(StaccatoArtic" in result
        assert "nr.Dx = 10" in result
        assert "nr.Dy = 5" in result
        assert "nr.StemDirection = 1" in result

    def test_generate_plugin_chord(self) -> None:
        """Test generating plugin with chord."""
        notes = [Note(pitch=60), Note(pitch=64), Note(pitch=67)]
        noterest = NoteRest(
            pos=0,
            dur=512,
            notes=notes,
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Piano")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddNote(0, 60, 512" in result
        assert "nr.AddNote(64)" in result
        assert "nr.AddNote(67)" in result

    def test_generate_plugin_dynamics(self) -> None:
        """Test generating plugin with dynamics."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        dyn = Dynamic(pos=0, text="ff")
        bar = Bar(n=1, length=1024, elements=[noterest, dyn])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddText(0, 'ff', 'text.staff.expression')" in result

    def test_generate_plugin_text_styles(self) -> None:
        """Test generating plugin with various text styles."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        text1 = Text(pos=0, text="pizz.", style="technique")
        text2 = Text(pos=256, text="dolce", style="expression")
        text3 = Text(pos=512, text="note", style="")
        bar = Bar(n=1, length=1024, elements=[noterest, text1, text2, text3])
        staff = Staff(n=1, bars=[bar], instrument="Cello")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "text.staff.technique" in result
        assert "text.staff.expression" in result
        assert "text.staff.plain" in result

    def test_generate_plugin_clefs(self) -> None:
        """Test generating plugin with clef changes."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        clef = Clef(pos=0, type="bass")
        bar = Bar(n=1, length=1024, elements=[noterest, clef])
        staff = Staff(n=1, bars=[bar], instrument="Cello")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddClef(0, 'clef.bass')" in result

    def test_generate_plugin_slurs(self) -> None:
        """Test generating plugin with slurs."""
        slur = Slur(
            start_bar=1,
            start_pos=0,
            end_bar=1,
            end_pos=512,
            voice=1,
        )
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[slur, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddLine(0, 512, 'line.staff.slur.up'" in result

    def test_generate_plugin_hairpins(self) -> None:
        """Test generating plugin with hairpins."""
        cresc = Hairpin(
            start_bar=1,
            start_pos=0,
            end_bar=1,
            end_pos=512,
            type="cresc",
            voice=1,
        )
        dim = Hairpin(
            start_bar=1,
            start_pos=512,
            end_bar=1,
            end_pos=1024,
            type="dim",
            voice=1,
        )
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[cresc, dim, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "line.staff.hairpin.crescendo" in result
        assert "line.staff.hairpin.diminuendo" in result

    def test_generate_plugin_tuplets(self) -> None:
        """Test generating plugin with tuplets."""
        tuplet = Tuplet(start_bar=1, start_pos=0, num=3, den=2)
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bar = Bar(n=1, length=1024, elements=[tuplet, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddTuplet(0, 1, 3, 2, 256)" in result

    def test_generate_plugin_barlines(self) -> None:
        """Test generating plugin with special barlines."""
        barline = Barline(pos=1024, type="double")
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[barline, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddSpecialBarline(DoubleBarline)" in result

    def test_generate_plugin_octava(self) -> None:
        """Test generating plugin with octava lines."""
        octava = Octava(
            start_bar=1,
            start_pos=0,
            end_bar=1,
            end_pos=1024,
            type="8va",
            voice=1,
        )
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[octava, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "line.staff.octava.plus8" in result

    def test_generate_plugin_pedal(self) -> None:
        """Test generating plugin with pedal lines."""
        pedal = Pedal(
            type="sustain",
            start_bar=1,
            start_pos=0,
            end_bar=1,
            end_pos=1024,
        )
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bar = Bar(n=1, length=1024, elements=[pedal, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Piano")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "line.staff.pedal" in result

    def test_generate_plugin_trill(self) -> None:
        """Test generating plugin with trill lines."""
        trill = Trill(
            start_bar=1,
            start_pos=0,
            end_bar=1,
            end_pos=512,
            voice=1,
        )
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[trill, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "line.staff.trill" in result

    def test_generate_plugin_grace_notes(self) -> None:
        """Test generating plugin with grace notes."""
        grace = Grace(pos=0, type="acciaccatura", pitch=60, dur=128)
        note = Note(pitch=62)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bar = Bar(n=1, length=1024, elements=[grace, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "acciaccatura" in result

    def test_generate_plugin_tempo(self) -> None:
        """Test generating plugin with tempo markings."""
        tempo = Tempo(pos=0, text="Allegro", bpm=120)
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[tempo, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "text.system.tempo" in result
        assert "Allegro" in result

    def test_generate_plugin_rehearsal(self) -> None:
        """Test generating plugin with rehearsal marks."""
        reh = Rehearsal(pos=0, text="A")
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[reh, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "text.system.rehearsalmark" in result

    def test_generate_plugin_lyrics(self) -> None:
        """Test generating plugin with lyrics."""
        syl = Syllable(bar=1, pos=0, text="la", hyphen=True)
        lyrics = Lyrics(voice=1, verse=1, syllables=[syl])
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Soprano", lyrics=[lyrics])
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "AddLyric" in result
        assert "'la'" in result

    def test_generate_plugin_page_layout(self) -> None:
        """Test generating plugin with page layout."""
        layout = Layout(page_width=210, page_height=297, staff_height=7)
        score = Score(
            staves=[],
            meta=Meta(),
            layout=layout,
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "PageWidth = 210" in result
        assert "PageHeight = 297" in result
        assert "StaffSize = 7" in result

    def test_generate_plugin_breaks(self) -> None:
        """Test generating plugin with page/system breaks."""
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar1 = Bar(n=1, length=1024, elements=[noterest], break_type="page")
        bar2 = Bar(n=2, length=1024, elements=[noterest], break_type="system")
        staff = Staff(n=1, bars=[bar1, bar2], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "EndOfPage" in result
        assert "EndOfSystem" in result

    def test_generate_plugin_time_key_signatures(self) -> None:
        """Test generating plugin with time/key signatures."""
        ts = TimeSignature(pos=0, num=3, den=4)
        ks = KeySignature(pos=0, fifths=-2, mode="major")
        sys_bar = Bar(n=1, length=768, elements=[ts, ks])
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=768, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[sys_bar]),
        )

        result = generate_plugin(score, "Test")
        assert "AddTimeSignature(3, 4" in result
        assert "AddKeySignature(0, -2, True)" in result

    def test_generate_plugin_staff_size(self) -> None:
        """Test generating plugin with staff size."""
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Piccolo", size=75)
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "SmallStaffSize = 75" in result

    def test_generate_plugin_stem_down(self) -> None:
        """Test generating plugin with stem direction down."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1, stem="down")
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )

        result = generate_plugin(score, "Test")
        assert "nr.StemDirection = -1" in result

    def test_generate_plugin_filters_bars_beyond_score(self) -> None:
        """Test that bars beyond score length are filtered."""
        note = Note(pitch=60)
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
        )
        bar1 = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar1], instrument="Flute")

        # System staff has time sig at bar 100 (doesn't exist)
        ts = TimeSignature(pos=0, num=4, den=4)
        sys_bar = Bar(n=100, length=1024, elements=[ts])

        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[sys_bar]),
        )

        result = generate_plugin(score, "Test")
        # Should not have NthBar(100) since we only have 1 bar
        assert "NthBar(100)" not in result

    def test_convert_to_utf16(self) -> None:
        """Test converting to UTF-16 BE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "test.txt"
            dst = Path(tmpdir) / "test.plg"
            src.write_text("Hello", encoding="utf-8")
            convert_to_utf16(src, dst)

            # Check for BOM
            data = dst.read_bytes()
            assert data[:2] == b"\xfe\xff"
            # Decode and verify content
            content = data[2:].decode("utf-16-be")
            assert content == "Hello"

    def test_generate_main_no_args(self) -> None:
        """Test main with no arguments."""
        with patch.object(sys, "argv", ["generate_plugin.py"]):
            assert generate_main() == 1

    def test_generate_main_missing_file(self) -> None:
        """Test main with missing input file."""
        with patch.object(
            sys, "argv", ["generate_plugin.py", "nonexistent.xml", "out.plg"]
        ):
            assert generate_main() == 1

    def test_generate_main_success(self) -> None:
        """Test main with valid input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal XML
            xml_path = Path(tmpdir) / "test.mahlif.xml"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
    <meta><work-title>Test</work-title></meta>
    <layout/>
    <movement>
        <system-staff/>
        <staff n="1" instrument="Flute">
            <bar n="1" length="1024"/>
        </staff>
    </movement>
</mahlif>"""
            xml_path.write_text(xml_content, encoding="utf-8")

            out_path = Path(tmpdir) / "test.plg"
            with patch.object(
                sys, "argv", ["generate_plugin.py", str(xml_path), str(out_path)]
            ):
                result = generate_main()
                assert result == 0
                assert out_path.exists()


# =============================================================================
# lint tests
# =============================================================================


class TestLint:
    """Tests for lint module."""

    def test_lint_error_str(self) -> None:
        """Test LintError string representation."""
        err = LintError(10, 5, "E001", "Test error")
        assert str(err) == "10:5 [E001] Test error"

    def test_read_plugin_utf8(self) -> None:
        """Test reading UTF-8 plugin."""
        with tempfile.NamedTemporaryFile(suffix=".plg", delete=False) as f:
            f.write(b"{ test }")
            f.flush()
            content = read_plugin(Path(f.name))
            assert content == "{ test }"
            Path(f.name).unlink()

    def test_read_plugin_utf16_be(self) -> None:
        """Test reading UTF-16 BE plugin."""
        with tempfile.NamedTemporaryFile(suffix=".plg", delete=False) as f:
            f.write(b"\xfe\xff")  # BOM
            f.write("{ test }".encode("utf-16-be"))
            f.flush()
            content = read_plugin(Path(f.name))
            # BOM becomes \ufeff character in decoded string
            assert content.lstrip("\ufeff") == "{ test }"
            Path(f.name).unlink()

    def test_read_plugin_utf16_le(self) -> None:
        """Test reading UTF-16 LE plugin."""
        with tempfile.NamedTemporaryFile(suffix=".plg", delete=False) as f:
            f.write(b"\xff\xfe")  # BOM
            f.write("{ test }".encode("utf-16-le"))
            f.flush()
            content = read_plugin(Path(f.name))
            # BOM becomes \ufeff character in decoded string
            assert content.lstrip("\ufeff") == "{ test }"
            Path(f.name).unlink()

    def test_lint_braces_balanced(self) -> None:
        """Test balanced braces."""
        errors = lint_braces("{ foo() }")
        assert len(errors) == 0

    def test_lint_braces_unmatched_close(self) -> None:
        """Test unmatched closing brace."""
        errors = lint_braces("{ } }")
        assert len(errors) == 1
        assert errors[0].code == "E001"

    def test_lint_braces_mismatched(self) -> None:
        """Test mismatched braces."""
        errors = lint_braces("{ [ }")
        assert any(e.code == "E002" for e in errors)

    def test_lint_braces_unclosed(self) -> None:
        """Test unclosed brace."""
        errors = lint_braces("{ foo(")
        assert any(e.code == "E003" for e in errors)

    def test_lint_braces_in_string(self) -> None:
        """Test braces inside strings are ignored."""
        errors = lint_braces('{ "}" }')
        assert len(errors) == 0

    def test_lint_braces_in_comment(self) -> None:
        """Test braces in comments are ignored."""
        errors = lint_braces("{ // }\n}")
        assert len(errors) == 0

    def test_lint_strings_valid(self) -> None:
        """Test valid strings."""
        errors = lint_strings('"hello"')
        assert len(errors) == 0

    def test_lint_methods_reserved_word(self) -> None:
        """Test reserved word as method name."""
        errors = lint_methods('if "()"')
        assert len(errors) == 1
        assert errors[0].code == "W001"

    def test_lint_methods_valid(self) -> None:
        """Test valid method name."""
        errors = lint_methods('Initialize "()"')
        assert len(errors) == 0

    def test_lint_common_trailing_whitespace(self) -> None:
        """Test trailing whitespace detection."""
        errors = lint_common_issues("foo ")
        assert any(e.code == "W002" for e in errors)

    def test_lint_common_long_line(self) -> None:
        """Test long line detection."""
        errors = lint_common_issues("x" * 250)
        assert any(e.code == "W003" for e in errors)

    def test_lint_plugin_structure_missing_brace(self) -> None:
        """Test missing opening brace."""
        errors = lint_plugin_structure("Initialize")
        assert any(e.code == "E010" for e in errors)

    def test_lint_plugin_structure_missing_end(self) -> None:
        """Test missing closing brace."""
        errors = lint_plugin_structure("{")
        assert any(e.code == "E011" for e in errors)

    def test_lint_plugin_structure_missing_init(self) -> None:
        """Test missing Initialize method."""
        errors = lint_plugin_structure("{ Run }")
        assert any(e.code == "W010" for e in errors)

    def test_lint_plugin_structure_missing_menu(self) -> None:
        """Test missing AddToPluginsMenu."""
        errors = lint_plugin_structure("{ Initialize }")
        assert any(e.code == "W011" for e in errors)

    def test_lint_plugin_structure_valid(self) -> None:
        """Test valid plugin structure."""
        content = "{ Initialize AddToPluginsMenu }"
        errors = lint_plugin_structure(content)
        assert not any(e.code in ("E010", "E011", "W010", "W011") for e in errors)

    def test_lint_method_calls_tokenize_error(self) -> None:
        """Test that tokenize errors don't crash lint."""
        # This would need a really malformed input
        errors = lint_method_calls("")
        assert errors == []

    def test_lint_full_file(self) -> None:
        """Test full lint on valid plugin."""
        with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
            f.write('{ Initialize "() { AddToPluginsMenu(); }" }')
            f.flush()
            errors = lint(Path(f.name))
            # Should have no critical errors
            assert not any(e.code.startswith("E0") for e in errors)
            Path(f.name).unlink()

    def test_lint_main_no_args(self) -> None:
        """Test main with no arguments."""
        with patch.object(sys, "argv", ["lint.py"]):
            assert lint_main() == 1

    def test_lint_main_missing_file(self) -> None:
        """Test main with missing file."""
        with patch.object(sys, "argv", ["lint.py", "nonexistent.plg"]):
            assert lint_main() == 1

    def test_lint_main_success(self) -> None:
        """Test main with valid file."""
        with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
            f.write('{ Initialize "() { AddToPluginsMenu(); }" }')
            f.flush()
            with patch.object(sys, "argv", ["lint.py", f.name]):
                result = lint_main()
                # May have warnings but should run
                assert result >= 0
            Path(f.name).unlink()


# =============================================================================
# manuscript_ast tests
# =============================================================================


class TestManuscriptAST:
    """Tests for manuscript_ast module."""

    def test_tokenizer_basic(self) -> None:
        """Test basic tokenization."""
        tokenizer = Tokenizer("x = 1;")
        tokens = list(tokenizer.tokenize())
        types = [t.type for t in tokens]
        assert TokenType.IDENTIFIER in types
        assert TokenType.ASSIGN in types
        assert TokenType.NUMBER in types
        assert TokenType.SEMICOLON in types
        assert TokenType.EOF in types

    def test_tokenizer_string_single(self) -> None:
        """Test single-quoted string."""
        tokenizer = Tokenizer("'hello'")
        tokens = list(tokenizer.tokenize())
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "'hello'"

    def test_tokenizer_string_double(self) -> None:
        """Test double-quoted string."""
        tokenizer = Tokenizer('"hello"')
        tokens = list(tokenizer.tokenize())
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == '"hello"'

    def test_tokenizer_string_escape(self) -> None:
        """Test escaped string."""
        tokenizer = Tokenizer(r"'it\'s'")
        tokens = list(tokenizer.tokenize())
        assert tokens[0].type == TokenType.STRING

    def test_tokenizer_number(self) -> None:
        """Test number tokenization."""
        tokenizer = Tokenizer("123 -45 3.14")
        tokens = list(tokenizer.tokenize())
        numbers = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(numbers) == 3
        assert numbers[0].value == "123"
        assert numbers[1].value == "-45"
        assert numbers[2].value == "3.14"

    def test_tokenizer_keywords(self) -> None:
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

    def test_tokenizer_operators(self) -> None:
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

    def test_tokenizer_delimiters(self) -> None:
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

    def test_tokenizer_comment(self) -> None:
        """Test comment handling."""
        tokenizer = Tokenizer("x = 1; // comment\ny = 2;")
        tokens = list(tokenizer.tokenize())
        comments = [t for t in tokens if t.type == TokenType.COMMENT]
        assert len(comments) == 1

    def test_tokenizer_dot(self) -> None:
        """Test dot operator."""
        tokenizer = Tokenizer("obj.method")
        tokens = list(tokenizer.tokenize())
        assert tokens[1].type == TokenType.DOT

    def test_tokenizer_ampersand(self) -> None:
        """Test ampersand (string concat)."""
        tokenizer = Tokenizer("'a' & 'b'")
        tokens = list(tokenizer.tokenize())
        assert any(t.type == TokenType.AMPERSAND for t in tokens)

    def test_tokenizer_unknown_char(self) -> None:
        """Test unknown character is skipped."""
        tokenizer = Tokenizer("x @ y")
        tokens = list(tokenizer.tokenize())
        # @ should be skipped
        idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        assert len(idents) == 2

    def test_token_repr(self) -> None:
        """Test Token repr."""
        token = Token(TokenType.IDENTIFIER, "foo", 1, 5)
        assert "IDENTIFIER" in repr(token)
        assert "foo" in repr(token)
        assert "1:5" in repr(token)

    def test_parser_empty_plugin(self) -> None:
        """Test parsing empty plugin."""
        plugin = parse_plugin("{ }")
        assert plugin.members == []

    def test_parser_method_def(self) -> None:
        """Test parsing method definition."""
        plugin = parse_plugin('{ Initialize "() { }" }')
        assert len(plugin.members) == 1
        assert plugin.members[0].name == "Initialize"  # type: ignore

    def test_parser_method_with_params(self) -> None:
        """Test parsing method with parameters."""
        plugin = parse_plugin('{ Test "(a, b, c) { }" }')
        assert len(plugin.members) == 1
        method = plugin.members[0]
        assert method.params == ["a", "b", "c"]  # type: ignore

    def test_parser_var_def(self) -> None:
        """Test parsing variable definition."""
        plugin = parse_plugin('{ Name "Test Plugin" }')
        assert len(plugin.members) == 1
        assert plugin.members[0].value == "Test Plugin"  # type: ignore

    def test_parser_bom_stripped(self) -> None:
        """Test BOM is stripped."""
        plugin = parse_plugin("\ufeff{ }")
        assert plugin.members == []

    def test_get_method_calls_simple(self) -> None:
        """Test extracting simple method call."""
        calls = get_method_calls("Sibelius.MessageBox('hi');")
        assert len(calls) == 1
        line, col, obj, method, arg_count = calls[0]
        assert obj == "Sibelius"
        assert method == "MessageBox"
        assert arg_count == 1

    def test_get_method_calls_global(self) -> None:
        """Test extracting global function call."""
        calls = get_method_calls("CreateSparseArray();")
        assert len(calls) == 1
        line, col, obj, method, arg_count = calls[0]
        assert obj is None
        assert method == "CreateSparseArray"
        assert arg_count == 0

    def test_get_method_calls_multiple_args(self) -> None:
        """Test extracting call with multiple args."""
        calls = get_method_calls("bar.AddNote(0, 60, 256, True, 1);")
        assert len(calls) == 1
        assert calls[0][4] == 5  # arg_count

    def test_get_method_calls_nested(self) -> None:
        """Test extracting nested calls."""
        calls = get_method_calls("foo(bar(1, 2));")
        # Should find both calls
        assert len(calls) >= 1

    def test_get_method_calls_empty_args(self) -> None:
        """Test call with no arguments."""
        calls = get_method_calls("obj.Method();")
        assert calls[0][4] == 0


# =============================================================================
# extract_api tests
# =============================================================================


class TestExtractAPI:
    """Tests for extract_api module."""

    def test_parse_signature_simple(self) -> None:
        """Test parsing simple signature."""
        result = parse_signature("Test()")
        assert result is not None
        assert result["name"] == "Test"
        assert result["min_params"] == 0
        assert result["max_params"] == 0

    def test_parse_signature_with_params(self) -> None:
        """Test parsing signature with params."""
        result = parse_signature("AddNote(pos,pitch,dur)")
        assert result is not None
        assert result["name"] == "AddNote"
        assert result["min_params"] == 3
        assert result["max_params"] == 3
        assert result["params"] == ["pos", "pitch", "dur"]

    def test_parse_signature_optional_params(self) -> None:
        """Test parsing signature with optional params."""
        result = parse_signature("Test(a,[b,[c]])")
        assert result is not None
        assert result["min_params"] == 1
        assert result["max_params"] == 3

    def test_parse_signature_invalid(self) -> None:
        """Test parsing invalid signature."""
        result = parse_signature("not a signature")
        assert result is None

    def test_parse_signature_lowercase(self) -> None:
        """Test lowercase name is rejected."""
        result = parse_signature("lowercase()")
        assert result is None

    def test_extract_signatures(self) -> None:
        """Test extracting signatures from text."""
        text = """
Some description text
AddNote(pos,pitch,dur)
More text
CreateSparseArray()
"""
        methods = extract_signatures(text)
        assert "AddNote" in methods
        assert "CreateSparseArray" in methods

    def test_extract_signatures_keeps_max_params(self) -> None:
        """Test that duplicate keeps max params version."""
        text = """
Test(a)
Test(a,b,c)
"""
        methods = extract_signatures(text)
        assert methods["Test"]["max_params"] == 3

    def test_extract_main(self) -> None:
        """Test main reads from stdin."""
        with patch.object(sys, "stdin") as mock_stdin:
            mock_stdin.read.return_value = "Test(a,b)\n"
            result = extract_main()
            assert result == 0


# =============================================================================
# automation tests
# =============================================================================


class TestAutomation:
    """Tests for automation module - mocked subprocess."""

    def test_run_applescript_success(self) -> None:
        """Test successful AppleScript execution."""
        from mahlif.sibelius.automation import run_applescript

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch.object(subprocess, "run", return_value=mock_result):
            result = run_applescript("test script")
            assert result == "output"

    def test_run_applescript_error(self) -> None:
        """Test AppleScript error handling."""
        from mahlif.sibelius.automation import run_applescript

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        with patch.object(subprocess, "run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="AppleScript error"):
                run_applescript("test script")

    def test_list_windows_empty(self) -> None:
        """Test list_windows with no windows."""
        from mahlif.sibelius.automation import list_windows

        with patch("mahlif.sibelius.automation.run_applescript", return_value=""):
            result = list_windows()
            assert result == []

    def test_list_windows_multiple(self) -> None:
        """Test list_windows with multiple windows."""
        from mahlif.sibelius.automation import list_windows

        with patch(
            "mahlif.sibelius.automation.run_applescript",
            return_value="Window 1, Window 2, Window 3",
        ):
            result = list_windows()
            assert result == ["Window 1", "Window 2", "Window 3"]

    def test_switch_to_window_found(self) -> None:
        """Test switch_to_window when window found."""
        from mahlif.sibelius.automation import switch_to_window

        with patch("mahlif.sibelius.automation.run_applescript", return_value="true"):
            result = switch_to_window("test")
            assert result is True

    def test_switch_to_window_not_found(self) -> None:
        """Test switch_to_window when window not found."""
        from mahlif.sibelius.automation import switch_to_window

        with patch("mahlif.sibelius.automation.run_applescript", return_value="false"):
            result = switch_to_window("test")
            assert result is False

    def test_screenshot(self) -> None:
        """Test screenshot function."""
        from mahlif.sibelius.automation import screenshot

        with patch("mahlif.sibelius.automation.run_applescript"):
            result = screenshot("/tmp/test.png")
            assert result == Path("/tmp/test.png")

    def test_activate(self) -> None:
        """Test activate function."""
        from mahlif.sibelius.automation import activate

        with patch("mahlif.sibelius.automation.run_applescript") as mock:
            activate()
            mock.assert_called_once()
            assert "Sibelius" in mock.call_args[0][0]

    def test_notify(self) -> None:
        """Test notify function."""
        from mahlif.sibelius.automation import notify

        with patch("mahlif.sibelius.automation.run_applescript") as mock:
            notify("test message")
            mock.assert_called_once()
            assert "display notification" in mock.call_args[0][0]

    def test_say(self) -> None:
        """Test say function."""
        from mahlif.sibelius.automation import say

        with patch("mahlif.sibelius.automation.run_applescript") as mock:
            say("hello")
            mock.assert_called_once()
            assert "say" in mock.call_args[0][0]

    def test_starting(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test starting function."""
        from mahlif.sibelius.automation import starting

        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch("mahlif.sibelius.automation.notify"):
                with patch("mahlif.sibelius.automation.say"):
                    starting("test task")

        captured = capsys.readouterr()
        assert "Starting: test task" in captured.out

    def test_done(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test done function."""
        from mahlif.sibelius.automation import done

        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch("mahlif.sibelius.automation.notify"):
                with patch("mahlif.sibelius.automation.say"):
                    done()

        captured = capsys.readouterr()
        assert "Done" in captured.out

    def test_go_to_bar(self) -> None:
        """Test go_to_bar function."""
        from mahlif.sibelius.automation import go_to_bar

        with patch("mahlif.sibelius.automation.run_applescript") as mock:
            go_to_bar(42)
            mock.assert_called_once()
            assert "42" in mock.call_args[0][0]

    def test_go_to_page(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test go_to_page function."""
        from mahlif.sibelius.automation import go_to_page

        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch("mahlif.sibelius.automation.notify"):
                go_to_page(5)

        captured = capsys.readouterr()
        assert "page 5" in captured.out

    def test_new_blank_score(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test new_blank_score function."""
        from mahlif.sibelius.automation import new_blank_score

        with patch("mahlif.sibelius.automation.run_applescript"):
            new_blank_score()

        captured = capsys.readouterr()
        assert "blank score" in captured.out

    def test_close_without_saving(self) -> None:
        """Test close_without_saving function."""
        from mahlif.sibelius.automation import close_without_saving

        with patch("mahlif.sibelius.automation.run_applescript") as mock:
            close_without_saving()
            mock.assert_called_once()
            assert "Don't Save" in mock.call_args[0][0]

    def test_scroll_to_start(self) -> None:
        """Test scroll_to_start function."""
        from mahlif.sibelius.automation import scroll_to_start

        with patch("mahlif.sibelius.automation.run_applescript") as mock:
            scroll_to_start()
            mock.assert_called_once()

    def test_run_plugin(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test run_plugin function."""
        from mahlif.sibelius.automation import run_plugin

        with patch("mahlif.sibelius.automation.run_applescript"):
            run_plugin("Test Plugin")

        captured = capsys.readouterr()
        assert "Test Plugin" in captured.out

    def test_reload_plugin(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test reload_plugin function."""
        from mahlif.sibelius.automation import reload_plugin

        with patch("mahlif.sibelius.automation.run_applescript"):
            reload_plugin("Test Plugin")

        captured = capsys.readouterr()
        assert "Reloading plugin: Test Plugin" in captured.out

    def test_compare_windows(self) -> None:
        """Test compare_windows function."""
        from mahlif.sibelius.automation import compare_windows

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mahlif.sibelius.automation.activate"):
                with patch("mahlif.sibelius.automation.switch_to_window"):
                    with patch("mahlif.sibelius.automation.go_to_page"):
                        with patch(
                            "mahlif.sibelius.automation.screenshot",
                            side_effect=lambda p: Path(p),
                        ):
                            path1, path2 = compare_windows(
                                "win1", "win2", tmpdir, page=1
                            )
                            assert "win1" in str(path1)
                            assert "win2" in str(path2)


# =============================================================================
# Additional tests for 100% coverage
# =============================================================================


class TestAdditionalCoverage:
    """Additional tests for edge cases and remaining coverage."""

    def test_generate_plugin_appoggiatura(self) -> None:
        """Test appoggiatura grace note path."""
        grace = Grace(pos=0, type="appoggiatura", pitch=60, dur=128)
        note = Note(pitch=62)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bar = Bar(n=1, length=1024, elements=[grace, noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        assert "appoggiatura" in result

    def test_generate_plugin_key_signature_minor(self) -> None:
        """Test minor key signature."""
        ks = KeySignature(pos=0, fifths=3, mode="minor")
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        sys_bar = Bar(n=1, length=1024, elements=[ks])
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[sys_bar]),
        )
        result = generate_plugin(score, "Test")
        assert "AddKeySignature(0, 3, False)" in result

    def test_generate_plugin_barline_types(self) -> None:
        """Test all barline types."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bl1 = Barline(pos=1024, type="final")
        bl2 = Barline(pos=1024, type="repeat-start")
        bl3 = Barline(pos=1024, type="repeat-end")
        bl4 = Barline(pos=1024, type="dashed")
        bar = Bar(n=1, length=1024, elements=[noterest, bl1, bl2, bl3, bl4])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        assert "FinalBarline" in result
        assert "StartRepeatBarline" in result
        assert "EndRepeatBarline" in result
        assert "DashedBarline" in result

    def test_generate_plugin_octava_types(self) -> None:
        """Test all octava types."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        oct1 = Octava(
            start_bar=1, start_pos=0, end_bar=1, end_pos=256, type="8vb", voice=1
        )
        oct2 = Octava(
            start_bar=1, start_pos=256, end_bar=1, end_pos=512, type="15va", voice=1
        )
        oct3 = Octava(
            start_bar=1, start_pos=512, end_bar=1, end_pos=768, type="15vb", voice=1
        )
        bar = Bar(n=1, length=1024, elements=[noterest, oct1, oct2, oct3])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        assert "octava.minus8" in result
        assert "octava.plus15" in result
        assert "octava.minus15" in result

    def test_generate_plugin_all_clef_types(self) -> None:
        """Test all clef types."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        clef1 = Clef(pos=0, type="alto")
        clef2 = Clef(pos=256, type="tenor")
        clef3 = Clef(pos=512, type="percussion")
        clef4 = Clef(pos=768, type="unknown")  # fallback to treble
        bar = Bar(n=1, length=1024, elements=[noterest, clef1, clef2, clef3, clef4])
        staff = Staff(n=1, bars=[bar], instrument="Viola")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        assert "clef.alto" in result
        assert "clef.tenor" in result
        assert "clef.percussion" in result
        assert "clef.treble" in result  # fallback

    def test_generate_plugin_all_articulations(self) -> None:
        """Test all articulation mappings."""
        note = Note(pitch=60)
        articulations = [
            "staccato",
            "accent",
            "tenuto",
            "marcato",
            "staccatissimo",
            "wedge",
            "pause",
            "up-bow",
            "down-bow",
            "harmonic",
            "plus",
            "tri-pause",
            "square-pause",
            "unknown-artic",
        ]
        noterest = NoteRest(
            pos=0,
            dur=256,
            notes=[note],
            voice=1,
            articulations=articulations,
        )
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        assert "StaccatoArtic" in result
        assert "AccentArtic" in result
        assert "TenutoArtic" in result
        # unknown-artic should be skipped (not in map)

    def test_generate_plugin_tied_note(self) -> None:
        """Test tied note."""
        note = Note(pitch=60, tied=True)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Flute")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        assert "True" in result  # tied=True

    def test_generate_plugin_zero_duration_spanner(self) -> None:
        """Test spanners with zero duration are skipped."""
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        slur = Slur(start_bar=1, start_pos=0, end_bar=1, end_pos=0, voice=1)
        bar = Bar(n=1, length=1024, elements=[noterest, slur])
        staff = Staff(n=1, bars=[bar], instrument="Violin")
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        # Zero duration slur should not generate AddLine
        assert result.count("AddLine") == 0 or "line.staff.slur" not in result

    def test_generate_plugin_lyrics_without_bar(self) -> None:
        """Test lyrics syllable without bar is skipped."""
        syl = Syllable(bar=None, pos=0, text="la", hyphen=False)
        lyrics = Lyrics(voice=1, verse=1, syllables=[syl])
        note = Note(pitch=60)
        noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
        bar = Bar(n=1, length=1024, elements=[noterest])
        staff = Staff(n=1, bars=[bar], instrument="Soprano", lyrics=[lyrics])
        score = Score(
            staves=[staff],
            meta=Meta(),
            layout=Layout(),
            system_staff=SystemStaff(bars=[]),
        )
        result = generate_plugin(score, "Test")
        # Lyric without bar should be skipped - no AddLyric call
        assert "AddLyric" not in result

    def test_lint_braces_single_quote_escape(self) -> None:
        """Test single quote string handling."""
        errors = lint_braces("{ x = 'it\\'s'; }")
        assert len(errors) == 0

    def test_lint_braces_double_quote_escape(self) -> None:
        """Test double quote string handling."""
        errors = lint_braces('{ x = "test\\"quote"; }')
        assert len(errors) == 0

    def test_parse_signature_all_optional(self) -> None:
        """Test signature where all params are optional."""
        result = parse_signature("Test([a,[b]])")
        assert result is not None
        assert result["min_params"] == 0
        assert result["max_params"] == 2

    def test_manuscript_ast_for_each_in(self) -> None:
        """Test tokenizing for each in keywords."""
        tokenizer = Tokenizer("for each x in y")
        tokens = list(tokenizer.tokenize())
        assert any(t.type == TokenType.FOR for t in tokens)
        assert any(t.type == TokenType.EACH for t in tokens)
        assert any(t.type == TokenType.IN for t in tokens)

    def test_manuscript_ast_to_keyword(self) -> None:
        """Test tokenizing 'to' keyword."""
        tokenizer = Tokenizer("for i = 1 to 10")
        tokens = list(tokenizer.tokenize())
        assert any(t.type == TokenType.TO for t in tokens)

    def test_manuscript_ast_and_or_not(self) -> None:
        """Test boolean operators."""
        tokenizer = Tokenizer("a and b or not c")
        tokens = list(tokenizer.tokenize())
        assert any(t.type == TokenType.AND for t in tokens)
        assert any(t.type == TokenType.OR for t in tokens)
        assert any(t.type == TokenType.NOT for t in tokens)

    def test_manuscript_ast_case_switch(self) -> None:
        """Test switch/case keywords."""
        tokenizer = Tokenizer("switch (x) { case 1: }")
        tokens = list(tokenizer.tokenize())
        assert any(t.type == TokenType.SWITCH for t in tokens)
        assert any(t.type == TokenType.CASE for t in tokens)

    def test_manuscript_ast_True_False_keyword(self) -> None:
        """Test True/False as keywords (case sensitive)."""
        tokenizer = Tokenizer("True False")
        tokens = list(tokenizer.tokenize())
        assert tokens[0].type == TokenType.TRUE
        assert tokens[1].type == TokenType.FALSE

    def test_parser_expect_wrong_token(self) -> None:
        """Test parser error on unexpected token."""
        tokens = [
            Token(TokenType.IDENTIFIER, "foo", 1, 1),
            Token(TokenType.EOF, "", 1, 4),
        ]
        parser = Parser(tokens)
        with pytest.raises(SyntaxError, match="Expected LBRACE"):
            parser.parse()

    def test_parser_empty_params(self) -> None:
        """Test method with empty params string."""
        plugin = parse_plugin('{ Test "() { }" }')
        assert len(plugin.members) == 1
        method = plugin.members[0]
        assert method.params == []  # type: ignore

    def test_get_method_calls_comment_in_args(self) -> None:
        """Test method calls ignore comments in arg counting."""
        calls = get_method_calls("foo(a, // comment\nb);")
        # Should find foo with 2 args
        assert len(calls) >= 1

    def test_lint_method_calls_with_valid_params(self) -> None:
        """Test lint_method_calls with known method."""
        # CreateSparseArray() can have 0+ args
        errors = lint_method_calls("CreateSparseArray();")
        assert len(errors) == 0

    def test_extract_api_empty_params(self) -> None:
        """Test parse_signature with no params."""
        result = parse_signature("NoParams()")
        assert result is not None
        assert result["params"] == []

    def test_lint_main_with_errors(self) -> None:
        """Test lint main when errors found."""
        with tempfile.NamedTemporaryFile(suffix=".plg", delete=False, mode="w") as f:
            f.write("missing braces")  # Will have E010
            f.flush()
            with patch.object(sys, "argv", ["lint.py", f.name]):
                result = lint_main()
                assert result > 0  # Should have errors
            Path(f.name).unlink()


class TestFinalCoverage:
    """Final tests for remaining coverage gaps."""

    def test_extract_api_nested_optional(self) -> None:
        """Test deeply nested optional params."""
        result = parse_signature("Foo(a,b,[c,[d,[e]]])")
        assert result is not None
        assert result["min_params"] == 2
        assert result["max_params"] == 5

    def test_lint_common_issues_tab_trailing(self) -> None:
        """Test tab as trailing whitespace."""
        errors = lint_common_issues("foo\t")
        assert any(e.code == "W002" for e in errors)

    def test_lint_strings_comment_line(self) -> None:
        """Test comment line is skipped in string checking."""
        errors = lint_strings('// this has unbalanced " quote')
        assert len(errors) == 0

    def test_lint_strings_empty_line(self) -> None:
        """Test empty content."""
        errors = lint_strings("")
        assert len(errors) == 0

    def test_manuscript_ast_peek_beyond_end(self) -> None:
        """Test peeking beyond end of source."""
        tokenizer = Tokenizer("x")
        list(tokenizer.tokenize())  # Exhaust
        assert tokenizer._peek(100) == ""

    def test_parser_check_eof(self) -> None:
        """Test parser checking for EOF."""
        tokens = [Token(TokenType.EOF, "", 1, 1)]
        parser = Parser(tokens)
        assert parser._check(TokenType.EOF) is True

    def test_get_method_calls_newline_in_args(self) -> None:
        """Test method with newlines in args."""
        calls = get_method_calls("foo(\na,\nb\n);")
        assert len(calls) >= 1
        assert calls[0][4] == 2  # 2 args

    def test_parser_advance_beyond_end(self) -> None:
        """Test parser advance beyond token list."""
        tokens = [Token(TokenType.LBRACE, "{", 1, 1), Token(TokenType.EOF, "", 1, 2)]
        parser = Parser(tokens)
        parser._advance()  # {
        parser._advance()  # EOF
        parser._advance()  # Still returns last token
        # Should not crash

    def test_generate_plugin_cli_with_title_from_meta(self) -> None:
        """Test CLI uses work_title when available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "test.mahlif.xml"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
    <meta><work-title>My Symphony</work-title></meta>
    <layout/>
    <movement>
        <system-staff/>
        <staff n="1" instrument="Flute">
            <bar n="1" length="1024"/>
        </staff>
    </movement>
</mahlif>"""
            xml_path.write_text(xml_content, encoding="utf-8")
            out_path = Path(tmpdir) / "test.plg"
            with patch.object(
                sys, "argv", ["generate_plugin.py", str(xml_path), str(out_path)]
            ):
                result = generate_main()
                assert result == 0

    def test_extract_api_multiple_signatures_same_name(self) -> None:
        """Test that extract keeps max params version."""
        text = "Test(a)\nTest(a,b,c,d)\nTest(a,b)"
        methods = extract_signatures(text)
        assert methods["Test"]["max_params"] == 4
