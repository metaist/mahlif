"""Tests for LilyPond conversion."""

from __future__ import annotations

from mahlif import parse
from mahlif import to_lilypond
from mahlif.lilypond.converter import _articulation_to_lily
from mahlif.lilypond.converter import _bar_rest
from mahlif.lilypond.converter import _barline_to_lily
from mahlif.lilypond.converter import _clef_to_lily
from mahlif.lilypond.converter import _convert_bar
from mahlif.lilypond.converter import _convert_movement
from mahlif.lilypond.converter import _convert_staff
from mahlif.lilypond.converter import _duration_to_lily
from mahlif.lilypond.converter import _key_to_lily
from mahlif.lilypond.converter import _note_to_lily
from mahlif.lilypond.converter import _noterest_to_lily
from mahlif.lilypond.converter import _pitch_to_lily
from mahlif.lilypond.converter import _time_to_lily
from mahlif.models import Bar
from mahlif.models import Barline
from mahlif.models import Clef
from mahlif.models import Dynamic
from mahlif.models import Hairpin
from mahlif.models import KeySignature
from mahlif.models import Layout
from mahlif.models import Meta
from mahlif.models import Movement
from mahlif.models import Note
from mahlif.models import NoteRest
from mahlif.models import Score
from mahlif.models import Slur
from mahlif.models import Staff
from mahlif.models import TimeSignature
from mahlif.models import Tuplet


class TestPitchConversion:
    """Test pitch to LilyPond conversion."""

    def test_basic(self) -> None:
        """Test pitch conversion for various pitches."""
        assert _pitch_to_lily(60) == "c'"  # Middle C
        assert _pitch_to_lily(61) == "cis'"  # C#
        assert _pitch_to_lily(72) == "c''"  # C5
        assert _pitch_to_lily(48) == "c"  # C3
        assert _pitch_to_lily(36) == "c,"  # C2

    def test_with_accidentals(self) -> None:
        """Test pitch conversion with explicit accidentals."""
        assert _pitch_to_lily(61, "#") == "cis'"  # C# at pitch 61
        assert _pitch_to_lily(63, "b") == "des'"  # Db at pitch 63 (D-1=Db)
        assert _pitch_to_lily(62, "x") == "disis'"  # D## at pitch 62
        assert _pitch_to_lily(70, "bb") == "aeses'"  # Abb at pitch 70 (A4)

    def test_unknown_accidental(self) -> None:
        """Test pitch with unknown accidental uses chromatic name."""
        # Unknown accidental should fall through and use base PITCH_NAMES
        result = _pitch_to_lily(61, "unknown")
        assert result == "cis'"  # Falls back to chromatic pitch name


class TestDurationConversion:
    """Test duration to LilyPond conversion."""

    def test_standard_durations(self) -> None:
        """Test standard duration conversion."""
        assert _duration_to_lily(64) == "16"
        assert _duration_to_lily(128) == "8"
        assert _duration_to_lily(256) == "4"
        assert _duration_to_lily(512) == "2"
        assert _duration_to_lily(1024) == "1"
        assert _duration_to_lily(2048) == "\\breve"

    def test_unknown_durations(self) -> None:
        """Test duration conversion for unknown durations."""
        # Should find closest match or default
        assert _duration_to_lily(100) == "8"  # Between 64 and 128, picks 128
        assert _duration_to_lily(5000) == "4"  # Beyond all, defaults to quarter


class TestClefConversion:
    """Test clef to LilyPond conversion."""

    def test_standard_clefs(self) -> None:
        """Test standard clef conversion."""
        assert _clef_to_lily("treble") == "treble"
        assert _clef_to_lily("bass") == "bass"
        assert _clef_to_lily("alto") == "alto"
        assert _clef_to_lily("tenor") == "tenor"

    def test_octave_clefs(self) -> None:
        """Test octave clef conversion."""
        assert _clef_to_lily("treble-8vb") == "treble_8"
        assert _clef_to_lily("treble-8va") == "treble^8"

    def test_other_clefs(self) -> None:
        """Test other clef types."""
        assert _clef_to_lily("percussion") == "percussion"
        assert _clef_to_lily("unknown") == "treble"  # Default


class TestKeyConversion:
    """Test key signature to LilyPond conversion."""

    def test_major_keys(self) -> None:
        """Test major key conversion."""
        assert _key_to_lily(0) == "c \\major"
        assert _key_to_lily(1) == "g \\major"
        assert _key_to_lily(-1) == "f \\major"
        assert _key_to_lily(4) == "e \\major"
        assert _key_to_lily(-4) == "aes \\major"

    def test_minor_keys(self) -> None:
        """Test minor key conversion."""
        assert _key_to_lily(0, "minor") == "a \\minor"
        assert _key_to_lily(3, "minor") == "fis \\minor"

    def test_extremes(self) -> None:
        """Test key signature at extremes."""
        assert _key_to_lily(-7) == "ces \\major"
        assert _key_to_lily(7) == "cis \\major"
        # Values beyond range should clamp
        assert _key_to_lily(-10) == "ces \\major"
        assert _key_to_lily(10) == "cis \\major"


class TestTimeConversion:
    """Test time signature to LilyPond conversion."""

    def test_common_times(self) -> None:
        """Test common time signature conversion."""
        assert _time_to_lily(4, 4) == "\\time 4/4"
        assert _time_to_lily(3, 4) == "\\time 3/4"
        assert _time_to_lily(6, 8) == "\\time 6/8"


class TestBarlineConversion:
    """Test barline to LilyPond conversion."""

    def test_standard_barlines(self) -> None:
        """Test standard barline conversion."""
        assert _barline_to_lily("single") == '\\bar "|"'
        assert _barline_to_lily("double") == '\\bar "||"'
        assert _barline_to_lily("final") == '\\bar "|."'

    def test_repeat_barlines(self) -> None:
        """Test repeat barline conversion."""
        assert _barline_to_lily("repeat-start") == '\\bar ".|:"'
        assert _barline_to_lily("repeat-end") == '\\bar ":|."'

    def test_special_barlines(self) -> None:
        """Test special barline types."""
        assert _barline_to_lily("invisible") == ""
        assert _barline_to_lily("unknown") == '\\bar "|"'


class TestArticulationConversion:
    """Test articulation to LilyPond conversion."""

    def test_standard_articulations(self) -> None:
        """Test standard articulation conversion."""
        assert _articulation_to_lily("staccato") == "-."
        assert _articulation_to_lily("accent") == "->"
        assert _articulation_to_lily("fermata") == "\\fermata"
        assert _articulation_to_lily("trill") == "\\trill"
        assert _articulation_to_lily("unknown") == ""


class TestBarRest:
    """Test full-bar rest generation."""

    def test_standard_rests(self) -> None:
        """Test standard full-bar rests."""
        assert _bar_rest(1024) == "R1"
        assert _bar_rest(512) == "R2"
        assert _bar_rest(256) == "R4"

    def test_dotted_rests(self) -> None:
        """Test dotted full-bar rests."""
        assert _bar_rest(768) == "R2."
        assert _bar_rest(384) == "R4."
        assert _bar_rest(1536) == "R1."

    def test_compound_rests(self) -> None:
        """Test compound meter rests."""
        assert _bar_rest(1280) == "R1*5/4"

    def test_unknown_length(self) -> None:
        """Test unknown bar length defaults to R1."""
        assert _bar_rest(9999) == "R1"


class TestNoteConversion:
    """Test note to LilyPond conversion."""

    def test_with_tie(self) -> None:
        """Test note with tie."""
        note = Note(pitch=60, tied=True)
        result = _note_to_lily(note, 256, [])
        assert result == "c'4~"

    def test_with_articulations(self) -> None:
        """Test note with articulations."""
        note = Note(pitch=60)
        result = _note_to_lily(note, 256, ["staccato", "accent"])
        assert result == "c'4-.->"


class TestNoteRestConversion:
    """Test NoteRest to LilyPond conversion."""

    def test_chord_with_tie(self) -> None:
        """Test chord with tied notes."""
        nr = NoteRest(
            pos=0,
            dur=256,
            notes=[Note(pitch=60, tied=True), Note(pitch=64), Note(pitch=67)],
        )
        result = _noterest_to_lily(nr)
        assert result == "<c' e' g'>4~"

    def test_chord_with_articulations(self) -> None:
        """Test chord with articulations."""
        nr = NoteRest(
            pos=0,
            dur=256,
            notes=[Note(pitch=60), Note(pitch=64)],
            articulations=["accent"],
        )
        result = _noterest_to_lily(nr)
        assert result == "<c' e'>4->"


class TestBarConversion:
    """Test bar to LilyPond conversion."""

    def test_with_elements(self) -> None:
        """Test bar conversion with various elements."""
        bar = Bar(
            n=1,
            length=1024,
            elements=[
                TimeSignature(pos=0, num=4, den=4),
                KeySignature(pos=0, fifths=0, mode="major"),
                Clef(pos=0, type="treble"),
                NoteRest(pos=0, dur=256, notes=[Note(pitch=60)]),
                Dynamic(pos=0, text="f"),
                Hairpin(type="cresc", start_bar=1, start_pos=0, end_bar=1, end_pos=512),
                Barline(pos=1024, type="double"),
            ],
        )
        result = _convert_bar(bar, {}, {})
        assert "\\time 4/4" in result
        assert "\\key c \\major" in result
        assert "\\clef treble" in result
        assert "c'4" in result
        assert "\\f" in result
        assert "\\<" in result
        assert '\\bar "||"' in result

    def test_with_dim_hairpin(self) -> None:
        """Test bar with diminuendo hairpin."""
        bar = Bar(
            n=1,
            length=1024,
            elements=[
                Hairpin(type="dim", start_bar=1, start_pos=0, end_bar=1, end_pos=512),
            ],
        )
        result = _convert_bar(bar, {}, {})
        assert "\\>" in result

    def test_empty(self) -> None:
        """Test empty bar gets full-bar rest."""
        bar = Bar(n=1, length=1024, elements=[])
        result = _convert_bar(bar, {}, {})
        assert "R1" in result

    def test_with_slur_and_tuplet(self) -> None:
        """Test bar with slur and tuplet (currently no-ops)."""
        bar = Bar(
            n=1,
            length=1024,
            elements=[
                Slur(start_bar=1, start_pos=0, end_bar=1, end_pos=256),
                Tuplet(start_bar=1, start_pos=0, num=3, den=2),
            ],
        )
        result = _convert_bar(bar, {}, {})
        # Slur and tuplet don't add output currently, bar is empty
        assert "R1" in result

    def test_with_invisible_barline(self) -> None:
        """Test bar with invisible barline followed by another element."""
        bar = Bar(
            n=1,
            length=1024,
            elements=[
                NoteRest(pos=0, dur=512, notes=[Note(pitch=60)]),
                Barline(pos=512, type="invisible"),  # Invisible barline mid-bar
                NoteRest(
                    pos=512, dur=512, notes=[Note(pitch=62)]
                ),  # Note after barline
            ],
        )
        result = _convert_bar(bar, {}, {})
        # Both notes are there, but invisible barline adds nothing
        assert "c'" in result
        assert "d'" in result
        assert "\\bar" not in result


class TestStaffConversion:
    """Test staff to LilyPond conversion."""

    def test_with_instrument(self) -> None:
        """Test staff conversion with instrument name."""
        staff = Staff(
            n=1,
            instrument="Violin",
            clef="treble",
            key_sig=2,
            bars=[Bar(n=1, length=1024, elements=[])],
        )
        result = _convert_staff(staff, 1)
        assert '\\new Staff = "Violin"' in result
        assert "\\clef treble" in result
        assert "\\key d \\major" in result

    def test_without_instrument(self) -> None:
        """Test staff conversion without instrument name."""
        staff = Staff(n=5, bars=[])
        result = _convert_staff(staff, 0)
        assert '\\new Staff = "Staff 5"' in result


class TestMovementConversion:
    """Test movement to LilyPond conversion."""

    def test_with_title(self) -> None:
        """Test movement conversion with title."""
        movement = Movement(
            n=1,
            title="Allegro",
            staves=[Staff(n=1, bars=[])],
        )
        result = _convert_movement(movement)
        assert "% Movement 1: Allegro" in result
        assert "\\score {" in result

    def test_without_title(self) -> None:
        """Test movement conversion without title."""
        movement = Movement(n=1, staves=[])
        result = _convert_movement(movement)
        assert "% Movement" not in result
        assert "\\score {" in result


class TestScoreConversion:
    """Test full score to LilyPond conversion."""

    def test_empty_score(self) -> None:
        """Convert empty score to LilyPond."""
        score = Score()
        lily = to_lilypond(score)
        assert '\\version "2.24.0"' in lily
        assert "\\header" in lily

    def test_with_metadata(self) -> None:
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

    def test_with_all_metadata(self) -> None:
        """Convert score with all metadata fields."""
        score = Score(
            meta=Meta(
                work_title="Title",
                composer="Composer",
                lyricist="Lyricist",
                arranger="Arranger",
                copyright="Copyright",
            )
        )
        lily = to_lilypond(score)
        assert 'title = "Title"' in lily
        assert 'composer = "Composer"' in lily
        assert 'poet = "Lyricist"' in lily
        assert 'arranger = "Arranger"' in lily
        assert 'copyright = "Copyright"' in lily

    def test_single_note(self) -> None:
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

    def test_chord(self) -> None:
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

    def test_rest(self) -> None:
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

    def test_multi_movement(self) -> None:
        """Test multi-movement score conversion."""
        score = Score(
            movements=[
                Movement(n=1, title="Allegro", staves=[Staff(n=1, bars=[])]),
                Movement(n=2, title="Adagio", staves=[Staff(n=1, bars=[])]),
            ]
        )
        lily = to_lilypond(score)
        assert "% Movement 1: Allegro" in lily
        assert "% Movement 2: Adagio" in lily
        # Two separate \score blocks
        assert lily.count("\\score {") == 2

    def test_multi_movement_layout(self) -> None:
        """Test that multi-movement score uses first movement's layout."""
        score = Score(
            movements=[
                Movement(
                    n=1, layout=Layout(page_width=100.0, page_height=200.0), staves=[]
                ),
                Movement(
                    n=2, layout=Layout(page_width=300.0, page_height=400.0), staves=[]
                ),
            ]
        )
        lily = to_lilypond(score)
        assert "100" in lily
        assert "200" in lily

    def test_multi_movement_empty_fallback(self) -> None:
        """Test multi-movement score with no movements uses default layout."""
        score = Score(movements=[], layout=Layout(page_width=500.0, page_height=600.0))
        # Manually set to trigger multi-movement path
        score.movements = []
        lily = to_lilypond(score)
        # Should use score.layout since no movements
        assert "500" in lily
