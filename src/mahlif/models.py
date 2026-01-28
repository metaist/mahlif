"""Data models for Mahlif XML."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Position:
    """Position offset in staff spaces."""

    dx: float = 0.0
    dy: float = 0.0


@dataclass
class Note:
    """A single note within a chord or standalone."""

    pitch: int  # MIDI pitch (sounding)
    written_pitch: int | None = None  # For transposing instruments
    diatonic: int = 0  # Diatonic pitch (line/space number)
    accidental: str = ""  # "", "#", "b", "x", "bb"
    tied: bool = False


@dataclass
class NoteRest:
    """A note, chord, or rest."""

    pos: int  # Position in ticks from bar start
    dur: int  # Duration in ticks (256 = quarter note)
    voice: int = 1
    hidden: bool = False
    offset: Position = field(default_factory=Position)
    # For notes/chords
    notes: list[Note] = field(default_factory=list)
    articulations: list[str] = field(default_factory=list)
    stem: Literal["auto", "up", "down"] = "auto"
    beam: Literal["auto", "none", "start", "continue", "end"] = "auto"

    @property
    def is_rest(self) -> bool:
        """Return True if this is a rest."""
        return len(self.notes) == 0

    @property
    def is_chord(self) -> bool:
        """Return True if this is a chord."""
        return len(self.notes) > 1


@dataclass
class Clef:
    """A clef change."""

    pos: int
    type: str  # treble, bass, alto, tenor, etc.
    offset: Position = field(default_factory=Position)


@dataclass
class KeySignature:
    """A key signature."""

    pos: int
    fifths: int  # -7 to +7 (negative = flats)
    mode: Literal["major", "minor"] = "major"


@dataclass
class TimeSignature:
    """A time signature."""

    pos: int
    num: int
    den: int


@dataclass
class Dynamic:
    """A dynamic marking."""

    pos: int
    text: str  # pp, p, mp, mf, f, ff, etc.
    voice: int = 1
    offset: Position = field(default_factory=Position)


@dataclass
class Text:
    """A text element."""

    pos: int
    text: str
    style: str = ""
    voice: int = 1
    offset: Position = field(default_factory=Position)


@dataclass
class Tempo:
    """A tempo marking."""

    pos: int
    text: str
    bpm: int | None = None
    offset: Position = field(default_factory=Position)


@dataclass
class Rehearsal:
    """A rehearsal mark."""

    pos: int
    text: str
    type: Literal["number", "letter", "custom"] = "custom"


@dataclass
class Slur:
    """A slur spanning notes."""

    start_bar: int
    start_pos: int
    end_bar: int
    end_pos: int
    voice: int = 1


@dataclass
class Hairpin:
    """A crescendo or diminuendo hairpin."""

    type: Literal["cresc", "dim"]
    start_bar: int
    start_pos: int
    end_bar: int
    end_pos: int
    voice: int = 1


@dataclass
class Tuplet:
    """A tuplet (triplet, etc.)."""

    start_bar: int
    start_pos: int
    num: int  # Actual notes
    den: int  # In the time of


@dataclass
class Barline:
    """A barline."""

    pos: int
    type: str  # single, double, final, repeat-start, repeat-end, etc.


@dataclass
class Octava:
    """An octave line (8va, 8vb, etc.)."""

    type: str  # 8va, 8vb, 15va, 15vb
    start_bar: int
    start_pos: int
    end_bar: int
    end_pos: int
    voice: int = 1


@dataclass
class Pedal:
    """A pedal marking (piano)."""

    type: str  # sustain, sostenuto, una-corda
    start_bar: int
    start_pos: int
    end_bar: int
    end_pos: int


@dataclass
class Trill:
    """A trill line."""

    start_bar: int
    start_pos: int
    end_bar: int
    end_pos: int
    voice: int = 1


@dataclass
class Grace:
    """A grace note."""

    pos: int
    type: str  # grace, acciaccatura, appoggiatura
    pitch: int
    dur: int
    voice: int = 1


@dataclass
class Syllable:
    """A lyric syllable."""

    pos: int
    text: str
    bar: int | None = None
    hyphen: bool = False
    melisma: bool = False


@dataclass
class Lyrics:
    """Lyrics for a voice."""

    voice: int
    verse: int
    syllables: list[Syllable] = field(default_factory=list)


@dataclass
class Bar:
    """A single bar/measure."""

    n: int  # Bar number
    length: int = 1024  # Length in ticks (default = 4/4)
    break_type: str | None = None  # "system", "page", or None
    elements: list[
        NoteRest
        | Clef
        | KeySignature
        | TimeSignature
        | Dynamic
        | Text
        | Slur
        | Hairpin
        | Tuplet
        | Barline
        | Octava
        | Pedal
        | Trill
        | Grace
        | Tempo
        | Rehearsal
    ] = field(default_factory=list)


@dataclass
class Staff:
    """A staff (instrument part)."""

    n: int
    instrument: str = ""
    instrument_short: str = ""
    full_name: str = ""  # Full instrument name (for display)
    short_name: str = ""  # Short instrument name (for subsequent systems)
    clef: str = "treble"
    key_sig: int = 0  # Initial key signature
    lines: int = 5
    size: int = 100  # Staff size percentage (100 = normal)
    bars: list[Bar] = field(default_factory=list)
    lyrics: list[Lyrics] = field(default_factory=list)


@dataclass
class SystemStaff:
    """System-wide elements (tempo, rehearsal marks, etc.)."""

    bars: list[Bar] = field(default_factory=list)


@dataclass
class Layout:
    """Page layout settings."""

    page_width: float = 210.0  # mm
    page_height: float = 297.0  # mm
    staff_height: float = 7.0  # mm


@dataclass
class Meta:
    """Score metadata."""

    work_title: str = ""
    composer: str = ""
    lyricist: str = ""
    arranger: str = ""
    copyright: str = ""
    publisher: str = ""
    source_file: str = ""
    source_format: str = ""
    duration_ms: int = 0


@dataclass
class Movement:
    """A movement within a larger work."""

    n: int
    title: str = ""
    layout: Layout = field(default_factory=Layout)
    staves: list[Staff] = field(default_factory=list)
    system_staff: SystemStaff = field(default_factory=SystemStaff)


@dataclass
class Score:
    """A complete musical score."""

    meta: Meta = field(default_factory=Meta)
    layout: Layout = field(default_factory=Layout)
    # Either movements OR direct staves (not both)
    movements: list[Movement] = field(default_factory=list)
    staves: list[Staff] = field(default_factory=list)
    system_staff: SystemStaff = field(default_factory=SystemStaff)

    @property
    def is_multi_movement(self) -> bool:
        """Return True if this is a multi-movement work."""
        return len(self.movements) > 0
