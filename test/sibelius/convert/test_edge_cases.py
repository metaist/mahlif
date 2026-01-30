"""Tests for edge cases and coverage in convert module."""

from __future__ import annotations

from mahlif.models import Bar
from mahlif.models import Barline
from mahlif.models import Clef
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
from mahlif.models import Score
from mahlif.models import Slur
from mahlif.models import Staff
from mahlif.models import Syllable
from mahlif.models import SystemStaff
from mahlif.models import Tempo
from mahlif.models import Text
from mahlif.models import TimeSignature
from mahlif.models import Trill
from mahlif.sibelius.convert import generate_plugin


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
    clef4 = Clef(pos=768, type="unknown")
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
    assert "clef.treble" in result


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
        pos=0, dur=256, notes=[note], voice=1, articulations=articulations
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
    assert "True" in result


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
    assert "AddLyric" not in result


def test_convert_rest_only_bar() -> None:
    """Test bar with only rests is skipped."""
    noterest = NoteRest(pos=0, dur=256, notes=[], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
    assert "NthBar(1)" not in result


def test_convert_chord_with_offsets() -> None:
    """Test chord with dx/dy offsets."""
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(
        pos=0, dur=256, notes=[note1, note2], voice=1, offset=Position(dx=10, dy=-5)
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
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(pos=0, dur=256, notes=[note1, note2], voice=1, stem="up")
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
    note1 = Note(pitch=60)
    note2 = Note(pitch=64)
    noterest = NoteRest(pos=0, dur=256, notes=[note1, note2], voice=1, stem="down")
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
    assert "line.staff.pedal" in result


def test_convert_rest_element() -> None:
    """Test that rest elements are skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    rest = NoteRest(pos=256, dur=256, notes=[], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest, rest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[]),
    )
    result = generate_plugin(score, "Test")
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
    assert "text.system.tempo" not in result


def test_convert_key_time_sig_in_bar() -> None:
    """Test that key/time signatures in staff bars are handled."""
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
    assert "AddNote" in result


def test_convert_system_staff_other_element() -> None:
    """Test that non-key/time elements in system staff are skipped."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    text = Text(pos=0, text="test", style="tempo")
    sys_bar = Bar(n=1, length=1024, elements=[text])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar]),
    )
    result = generate_plugin(score, "Test")
    assert "AddNote" in result


def test_convert_system_staff_mixed_elements() -> None:
    """Test system staff bar with both key sig and other elements."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Flute")
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
    assert "AddKeySignature" in result


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
    """Test layout with all dimensions zero."""
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
    """Test chord with unknown articulation."""
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
    assert "StaccatoArtic" in result
    assert "unknown-artic" not in result


def test_convert_empty_system_staff_bars() -> None:
    """Test when system_staff.bars doesn't match staff bar."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest], break_type="page")
    staff = Staff(n=1, bars=[bar], instrument="Flute")
    ts = TimeSignature(pos=0, num=3, den=4)
    sys_bar = Bar(n=2, length=768, elements=[ts])
    score = Score(
        staves=[staff],
        meta=Meta(),
        layout=Layout(),
        system_staff=SystemStaff(bars=[sys_bar]),
    )
    result = generate_plugin(score, "Test")
    assert "BreakType = EndOfPage" in result


def test_system_staff_tempo_with_text() -> None:
    """Test Tempo element with text in system staff."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
    system_bar = Bar(n=1, length=1024, elements=[Tempo(pos=0, text="Allegro", bpm=120)])
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
    system_bar = Bar(n=1, length=1024, elements=[Barline(pos=0, type="double")])
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
        n=1, length=1024, elements=[Barline(pos=0, type="unknown-barline-type")]
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
    assert "BreakType" not in result


def test_system_staff_bar_number_mismatch() -> None:
    """Test when system staff has different bar numbers."""
    note = Note(pitch=60)
    noterest = NoteRest(pos=0, dur=256, notes=[note], voice=1)
    bar = Bar(n=1, length=1024, elements=[noterest])
    staff = Staff(n=1, bars=[bar], instrument="Piano")
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
