"""Tests for score-to-plugin conversion."""

from __future__ import annotations

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
from mahlif.sibelius.convert import generate_plugin


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
    noterest = NoteRest(pos=0, dur=512, notes=notes, voice=1)
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
    slur = Slur(start_bar=1, start_pos=0, end_bar=1, end_pos=512, voice=1)
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
        start_bar=1, start_pos=0, end_bar=1, end_pos=512, type="cresc", voice=1
    )
    dim = Hairpin(
        start_bar=1, start_pos=512, end_bar=1, end_pos=1024, type="dim", voice=1
    )
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
        start_bar=1, start_pos=0, end_bar=1, end_pos=1024, type="8va", voice=1
    )
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    pedal = Pedal(type="sustain", start_bar=1, start_pos=0, end_bar=1, end_pos=1024)
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
    trill = Trill(start_bar=1, start_pos=0, end_bar=1, end_pos=512, voice=1)
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
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
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar1 = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar1], instrument="Flute")
    ts = TimeSignature(pos=0, num=4, den=4)
    sys_bar = Bar(n=100, length=1024, elements=[ts])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar]),
    )

    result = generate_plugin(score, "Test")
    assert "NthBar(100)" not in result
