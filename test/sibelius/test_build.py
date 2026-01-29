"""Tests for Sibelius convert/build modules."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


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
from mahlif.sibelius.convert import ARTICULATION_MAP
from mahlif.sibelius.convert import _calc_spanner_duration
from mahlif.sibelius.convert import convert_to_utf16
from mahlif.sibelius.convert import escape_str
from mahlif.sibelius.convert import generate_plugin
from mahlif.sibelius.convert import main as generate_main
from mahlif.sibelius.convert import write_plugin


def test_escape_str_basic() -> None:
    """Test basic string escaping."""
    assert escape_str("hello") == "hello"
    assert escape_str("it's") == "it\\'s"
    assert escape_str("back\\slash") == "back\\\\slash"
    assert escape_str("it's a\\b") == "it\\'s a\\\\b"


def test_calc_spanner_duration_same_bar() -> None:
    """Test duration calculation within same bar."""
    result = _calc_spanner_duration(1, 0, 1, 256, 1024)
    assert result == 256


def test_calc_spanner_duration_cross_bar() -> None:
    """Test duration calculation across bars."""
    # Start bar 1, pos 512 to end bar 3, pos 256
    # bar_length = 1024
    # remaining in bar 1: 1024 - 512 = 512
    # full bar 2: 1024
    # end in bar 3: 256
    # total: 512 + 1024 + 256 = 1792
    result = _calc_spanner_duration(1, 512, 3, 256, 1024)
    assert result == 1792


def test_articulation_map_coverage() -> None:
    """Test that articulation map has expected entries."""
    assert "staccato" in ARTICULATION_MAP
    assert "fermata" in ARTICULATION_MAP
    assert ARTICULATION_MAP["fermata"] == "PauseArtic"
    assert "up-bow" in ARTICULATION_MAP
    assert "down-bow" in ARTICULATION_MAP


def test_convert_empty_score() -> None:
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


def test_convert_single_staff_with_notes() -> None:
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
    assert (
        "CreateInstrument('instrument.other.trebleclef', True, 'Flute', 'Fl.')"
        in result
    )
    assert "AddNote(0, 60, 256" in result
    assert "SetArticulation(StaccatoArtic" in result
    assert "nr.Dx = 10" in result
    assert "nr.Dy = 5" in result
    assert "nr.StemDirection = 1" in result


def test_convert_chord() -> None:
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


def test_convert_dynamics() -> None:
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


def test_convert_text_styles() -> None:
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


def test_convert_clefs() -> None:
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


def test_convert_slurs() -> None:
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


def test_convert_hairpins() -> None:
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


def test_convert_tuplets() -> None:
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


def test_convert_barlines() -> None:
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
    assert "AddSpecialBarline(SpecialBarlineDouble)" in result


def test_convert_octava() -> None:
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


def test_convert_pedal() -> None:
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


def test_convert_trill() -> None:
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


def test_convert_grace_notes() -> None:
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


def test_convert_tempo() -> None:
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


def test_convert_rehearsal() -> None:
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


def test_convert_lyrics() -> None:
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


def test_convert_page_layout() -> None:
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


def test_convert_breaks() -> None:
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


def test_convert_time_key_signatures() -> None:
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


def test_convert_staff_size() -> None:
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


def test_convert_stem_down() -> None:
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


def test_convert_filters_bars_beyond_score() -> None:
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


def test_convert_to_utf16() -> None:
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


def test_write_plugin() -> None:
    """Test write_plugin writes UTF-16 BE with BOM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "test.plg"
        write_plugin(dst, "Test content")

        # Check for BOM
        data = dst.read_bytes()
        assert data[:2] == b"\xfe\xff"
        # Decode and verify content
        content = data[2:].decode("utf-16-be")
        assert content == "Test content"


def test_generate_main_no_args() -> None:
    """Test main with no arguments."""
    with patch.object(sys, "argv", ["convert.py"]):
        assert generate_main() == 1


def test_generate_main_missing_file() -> None:
    """Test main with missing input file."""
    with patch.object(sys, "argv", ["convert.py", "nonexistent.xml", "out.plg"]):
        assert generate_main() == 1


def test_generate_main_success() -> None:
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
        with patch.object(sys, "argv", ["convert.py", str(xml_path), str(out_path)]):
            result = generate_main()
            assert result == 0
            assert out_path.exists()


# =============================================================================
# lint tests
# =============================================================================


def test_convert_appoggiatura() -> None:
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


def test_convert_key_signature_minor() -> None:
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


def test_convert_barline_types() -> None:
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
    assert "SpecialBarlineFinal" in result
    assert "SpecialBarlineStartRepeat" in result
    assert "SpecialBarlineEndRepeat" in result
    assert "SpecialBarlineDashed" in result


def test_convert_octava_types() -> None:
    """Test all octava types."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    oct1 = Octava(start_bar=1, start_pos=0, end_bar=1, end_pos=256, type="8vb", voice=1)
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


def test_convert_all_clef_types() -> None:
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


def test_convert_all_articulations() -> None:
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


def test_convert_tied_note() -> None:
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


def test_convert_zero_duration_spanner() -> None:
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


def test_convert_lyrics_without_bar() -> None:
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


def test_convert_cli_with_title_from_meta() -> None:
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
        with patch.object(sys, "argv", ["convert.py", str(xml_path), str(out_path)]):
            result = generate_main()
            assert result == 0


def test_convert_rest_only_bar() -> None:
    """Test bar with only rests is skipped."""
    # Line 185: has_notes is False, continue
    noterest = NoteRest(pos=0, dur=256, notes=[], voice=1)  # Rest
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Bar should be skipped, no NthBar call
    assert "NthBar(1)" not in result


def test_convert_chord_with_offsets() -> None:
    """Test chord with dx/dy offsets."""
    # Lines 213, 215: elem.offset.dx != 0 and elem.offset.dy != 0
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(
        pos=0,
        dur=256,
        notes=[note1, note2],
        voice=1,
        offset=Position(dx=10, dy=-5),
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
    assert "nr.Dx = 10" in result
    assert "nr.Dy = -5" in result


def test_convert_chord_with_stem_up() -> None:
    """Test chord with stem direction up."""
    # Line 218: elem.stem == "up"
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(
        pos=0,
        dur=256,
        notes=[note1, note2],
        voice=1,
        stem="up",
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
    assert "StemDirection = 1" in result


def test_convert_chord_with_stem_down() -> None:
    """Test chord with stem direction down."""
    # Line 220: elem.stem == "down"
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(
        pos=0,
        dur=256,
        notes=[note1, note2],
        voice=1,
        stem="down",
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
    assert "StemDirection = -1" in result


def test_convert_chord_with_articulations() -> None:
    """Test chord with articulations."""
    # Lines 207-208: articulations in chord path
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(
        pos=0,
        dur=256,
        notes=[note1, note2],
        voice=1,
        articulations=["staccato", "accent"],
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
    assert "StaccatoArtic" in result
    assert "AccentArtic" in result


def test_convert_with_page_layout() -> None:
    """Test generating plugin with page dimensions set."""
    # Lines 150->163: page_width/height > 0
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    layout = Layout(page_width=210, page_height=297, staff_height=7)
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=layout,
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "PageWidth = 210" in result
    assert "PageHeight = 297" in result
    assert "StaffSize = 7" in result


def test_convert_with_partial_layout() -> None:
    """Test layout with only some dimensions."""
    # Test branch where only width is set
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    layout = Layout(page_width=210, page_height=0, staff_height=0)
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=layout,
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "PageWidth = 210" in result
    assert "PageHeight" not in result


def test_convert_zero_duration_hairpin() -> None:
    """Test hairpin with zero duration is skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    hairpin = Hairpin(
        start_bar=1, start_pos=0, end_bar=1, end_pos=0, type="cresc", voice=1
    )
    bar = Bar(n=1, length=1024, elements=[noterest, hairpin])
    staff = Staff(n=1, bars=[bar], instrument="Violin")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Zero duration hairpin should not generate AddLine
    assert "hairpin" not in result


def test_convert_zero_duration_trill() -> None:
    """Test trill with zero duration is skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    trill = Trill(start_bar=1, start_pos=0, end_bar=1, end_pos=0, voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest, trill])
    staff = Staff(n=1, bars=[bar], instrument="Violin")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "trill" not in result


def test_convert_zero_duration_octava() -> None:
    """Test octava with zero duration is skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    octava = Octava(start_bar=1, start_pos=0, end_bar=1, end_pos=0, type="8va", voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest, octava])
    staff = Staff(n=1, bars=[bar], instrument="Violin")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "octava" not in result


def test_convert_zero_duration_pedal() -> None:
    """Test pedal with zero duration is skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    pedal = Pedal(type="sustain", start_bar=1, start_pos=0, end_bar=1, end_pos=0)
    bar = Bar(n=1, length=1024, elements=[noterest, pedal])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "pedal" not in result


def test_convert_unknown_barline_type() -> None:
    """Test unknown barline type is skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    barline = Barline(pos=1024, type="unknown-type")
    bar = Bar(n=1, length=1024, elements=[noterest, barline])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Unknown barline should not generate AddSpecialBarline
    assert "AddSpecialBarline" not in result


def test_convert_unknown_octava_type() -> None:
    """Test unknown octava type falls back to plus8."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    octava = Octava(
        start_bar=1, start_pos=0, end_bar=1, end_pos=256, type="unknown", voice=1
    )
    bar = Bar(n=1, length=1024, elements=[noterest, octava])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Unknown octava falls back to plus8
    assert "octava.plus8" in result


def test_convert_pedal_always_uses_generic_style() -> None:
    """Test pedal type doesn't affect output style."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    pedal = Pedal(type="sostenuto", start_bar=1, start_pos=0, end_bar=1, end_pos=256)
    bar = Bar(n=1, length=1024, elements=[noterest, pedal])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # All pedal types use same style
    assert "line.staff.pedal" in result


def test_convert_rest_element() -> None:
    """Test that rest elements are skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    rest = NoteRest(pos=256, dur=256, notes=[], voice=1)  # Rest
    bar = Bar(n=1, length=1024, elements=[noterest, rest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Rest should be skipped, only one AddNote call
    assert result.count("AddNote") == 1


def test_convert_tempo_without_text() -> None:
    """Test that tempo without text is skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    tempo = Tempo(pos=0, text="", bpm=120)
    bar = Bar(n=1, length=1024, elements=[noterest, tempo])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Tempo without text should not add text.system.tempo
    assert "text.system.tempo" not in result


def test_convert_key_time_sig_in_bar() -> None:
    """Test that key/time signatures in staff bars are skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    ks = KeySignature(pos=0, fifths=2, mode="major")
    ts = TimeSignature(pos=0, num=4, den=4)
    bar = Bar(n=1, length=1024, elements=[noterest, ks, ts])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Key/time sigs in staff bars should be handled at system level only
    # Check that we don't crash and the note is still added
    assert "AddNote" in result


def test_convert_system_staff_other_element() -> None:
    """Test that non-key/time elements in system staff are skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    # Put a text element in system staff (should be skipped)
    text = Text(pos=0, text="test", style="tempo")
    sys_bar = Bar(n=1, length=1024, elements=[text])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar]),
    )
    result = generate_plugin(score, "Test")
    # Text in system staff should not generate anything
    assert "AddNote" in result


def test_convert_system_staff_mixed_elements() -> None:
    """Test system staff bar with both key sig and other elements."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    # Put both key signature and text in same system staff bar
    ks = KeySignature(pos=0, fifths=2, mode="major")
    text = Text(pos=0, text="test", style="tempo")
    sys_bar = Bar(n=1, length=1024, elements=[ks, text])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar]),
    )
    result = generate_plugin(score, "Test")
    # Key sig should be added, text should be skipped
    assert "AddKeySignature" in result


# =============================================================================
# Robustness tests for malformed/edge case inputs
# =============================================================================


def test_layout_zero_width_positive_height() -> None:
    """Test layout with width=0 but height>0."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    layout = Layout(page_width=0, page_height=297, staff_height=0)
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=layout,
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "PageHeight = 297" in result
    assert "PageWidth" not in result


def test_layout_all_zero() -> None:
    """Test layout with all dimensions zero (skip layout block)."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    layout = Layout(page_width=0, page_height=0, staff_height=0)
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=layout,
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "docSetup" not in result


def test_chord_with_unknown_articulation() -> None:
    """Test chord (not single note) with unknown articulation."""
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(
        pos=0,
        dur=256,
        notes=[note1, note2],
        voice=1,
        articulations=["unknown-artic", "staccato"],
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
    # Should have staccato but not unknown-artic
    assert "StaccatoArtic" in result
    assert "unknown-artic" not in result


def test_convert_empty_system_staff_bars() -> None:
    """Test when system_staff.bars iteration completes without match."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest], break_type="page")
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    # System staff has bar 2, but we're looking for bar 1 (from break)
    ts = TimeSignature(pos=0, num=3, den=4)
    sys_bar = Bar(n=2, length=768, elements=[ts])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar]),
    )
    result = generate_plugin(score, "Test")
    # Should process bar 1 for break, but system staff bar 2 doesn't match
    assert "BreakType = EndOfPage" in result


def test_system_staff_tempo_with_text() -> None:
    """Test Tempo element with text in system staff."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    system_bar = Bar(
        n=1,
        length=1024,
        elements=[Tempo(pos=0, text="Allegro", bpm=120)],
    )
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[system_bar]),
    )
    result = generate_plugin(score, "Test")
    assert "text.system.tempo" in result
    assert "Allegro" in result


def test_system_staff_barline() -> None:
    """Test Barline element in system staff."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    system_bar = Bar(
        n=1,
        length=1024,
        elements=[Barline(pos=0, type="double")],
    )
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[system_bar]),
    )
    result = generate_plugin(score, "Test")
    assert "SpecialBarlineDouble" in result


def test_system_staff_barline_unknown_type() -> None:
    """Test Barline with unknown type in system staff."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    system_bar = Bar(
        n=1,
        length=1024,
        elements=[Barline(pos=0, type="unknown-barline-type")],
    )
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[system_bar]),
    )
    result = generate_plugin(score, "Test")
    assert "SpecialBarline" not in result


def test_grace_note_unknown_type() -> None:
    """Test grace note with unknown type."""
    grace = Grace(pos=0, type="unknown-grace", pitch=60, dur=128)
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
    # Unknown grace type should not generate any grace comment
    assert "acciaccatura" not in result
    assert "appoggiatura" not in result


def test_unknown_break_type() -> None:
    """Test bar with unknown break type."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest], break_type="unknown-break")
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    # Unknown break type should not generate BreakType assignment
    assert "BreakType" not in result


def test_system_staff_bar_number_mismatch() -> None:
    """Test when system staff has different bar numbers."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    # System staff has bar 5, but staff only has bar 1
    system_bar = Bar(n=5, length=1024, elements=[])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[system_bar]),
    )
    result = generate_plugin(score, "Test")
    assert isinstance(result, str)


def test_system_staff_multiple_bars_partial_match() -> None:
    """Test system staff with multiple bars, some matching."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar1 = Bar(n=1, length=1024, elements=[noterest])
    bar2 = Bar(n=2, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar1, bar2], instrument="Piano")
    # System staff has bars 1, 3 (bar 2 missing, bar 3 extra)
    sys_bar1 = Bar(n=1, length=1024, elements=[])
    sys_bar3 = Bar(n=3, length=1024, elements=[])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar1, sys_bar3]),
    )
    result = generate_plugin(score, "Test")
    assert isinstance(result, str)
