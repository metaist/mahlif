"""Convert Mahlif Score to LilyPond format."""

from __future__ import annotations

from mahlif.models import (
    Bar,
    Barline,
    Clef,
    Dynamic,
    Hairpin,
    KeySignature,
    Movement,
    Note,
    NoteRest,
    Score,
    Slur,
    Staff,
    TimeSignature,
    Tuplet,
)

# MIDI pitch to LilyPond note name mapping
# Pitch 60 = middle C = c'
PITCH_NAMES = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]

# Duration in ticks to LilyPond duration
# 256 = quarter note, 512 = half, 1024 = whole, etc.
DURATION_MAP = {
    64: "16",
    96: "16.",
    128: "8",
    192: "8.",
    256: "4",
    384: "4.",
    512: "2",
    768: "2.",
    1024: "1",
    1536: "1.",
    2048: "\\breve",
}


def _pitch_to_lily(pitch: int, accidental: str = "") -> str:
    """Convert MIDI pitch to LilyPond note name.

    Args:
        pitch: MIDI pitch number (60 = middle C)
        accidental: Accidental from source ("", "#", "b", "x", "bb")

    Returns:
        LilyPond note name with octave marks
    """
    octave = (pitch // 12) - 4  # LilyPond octave (c' = octave 1 = MIDI 60)
    note_index = pitch % 12

    # Base note name
    name = PITCH_NAMES[note_index]

    # Handle explicit accidentals from source
    # This overrides the chromatic pitch-based accidental
    if accidental:
        base_names = ["c", "c", "d", "d", "e", "f", "f", "g", "g", "a", "a", "b"]
        base_name = base_names[note_index]
        match accidental:
            case "#":
                name = base_name + "is"
            case "b":
                name = base_name + "es"
            case "x":
                name = base_name + "isis"
            case "bb":
                name = base_name + "eses"
            case _:
                # Unknown accidental - keep chromatic pitch name
                pass

    # Add octave marks
    if octave > 0:
        name += "'" * octave
    elif octave < 0:
        name += "," * (-octave)

    return name


def _duration_to_lily(dur: int) -> str:
    """Convert duration in ticks to LilyPond duration.

    Args:
        dur: Duration in ticks (256 = quarter note)

    Returns:
        LilyPond duration string
    """
    if dur in DURATION_MAP:
        return DURATION_MAP[dur]

    # Try to find closest match
    for d, ly in sorted(DURATION_MAP.items()):
        if d >= dur:
            return ly

    return "4"  # Default to quarter note


def _clef_to_lily(clef: str) -> str:
    """Convert clef name to LilyPond."""
    clef_map = {
        "treble": "treble",
        "bass": "bass",
        "alto": "alto",
        "tenor": "tenor",
        "treble-8vb": "treble_8",
        "treble-8va": "treble^8",
        "bass-8vb": "bass_8",
        "bass-8va": "bass^8",
        "percussion": "percussion",
    }
    return clef_map.get(clef, "treble")


def _key_to_lily(fifths: int, mode: str = "major") -> str:
    """Convert key signature to LilyPond.

    Args:
        fifths: Number of sharps (positive) or flats (negative)
        mode: "major" or "minor"

    Returns:
        LilyPond key specification
    """
    major_keys = [
        "ces",
        "ges",
        "des",
        "aes",
        "ees",
        "bes",
        "f",
        "c",
        "g",
        "d",
        "a",
        "e",
        "b",
        "fis",
        "cis",
    ]
    minor_keys = [
        "aes",
        "ees",
        "bes",
        "f",
        "c",
        "g",
        "d",
        "a",
        "e",
        "b",
        "fis",
        "cis",
        "gis",
        "dis",
        "ais",
    ]

    index = fifths + 7  # -7 to +7 -> 0 to 14
    index = max(0, min(14, index))

    if mode == "minor":
        return f"{minor_keys[index]} \\minor"
    return f"{major_keys[index]} \\major"


def _time_to_lily(num: int, den: int) -> str:
    """Convert time signature to LilyPond."""
    return f"\\time {num}/{den}"


def _barline_to_lily(barline_type: str) -> str:
    """Convert barline type to LilyPond."""
    barline_map = {
        "single": "|",
        "double": "||",
        "final": "|.",
        "repeat-start": ".|:",
        "repeat-end": ":|.",
        "repeat-both": ":|.|:",
        "dashed": "!",
        "invisible": "",
    }
    bar = barline_map.get(barline_type, "|")
    if bar:
        return f'\\bar "{bar}"'
    return ""


def _articulation_to_lily(art: str) -> str:
    """Convert articulation name to LilyPond."""
    art_map = {
        "staccato": "-.",
        "staccatissimo": "-!",
        "tenuto": "--",
        "accent": "->",
        "marcato": "-^",
        "fermata": "\\fermata",
        "long-fermata": "\\longfermata",
        "short-fermata": "\\shortfermata",
        "up-bow": "\\upbow",
        "down-bow": "\\downbow",
        "harmonic": "\\flageolet",
        "trill": "\\trill",
        "arpeggio": "\\arpeggio",
    }
    return art_map.get(art, "")


def _note_to_lily(note: Note, dur: int, articulations: list[str]) -> str:
    """Convert a single note to LilyPond."""
    name = _pitch_to_lily(note.pitch, note.accidental)
    duration = _duration_to_lily(dur)

    result = f"{name}{duration}"

    # Add articulations
    for art in articulations:
        result += _articulation_to_lily(art)

    # Add tie
    if note.tied:
        result += "~"

    return result


def _noterest_to_lily(nr: NoteRest) -> str:
    """Convert a NoteRest to LilyPond."""
    dur = _duration_to_lily(nr.dur)

    if nr.is_rest:
        if nr.hidden:
            return f"s{dur}"  # Spacer rest
        return f"r{dur}"

    if nr.is_chord:
        # Chord: <c e g>4
        notes = " ".join(_pitch_to_lily(n.pitch, n.accidental) for n in nr.notes)
        result = f"<{notes}>{dur}"

        # Add articulations
        for art in nr.articulations:
            result += _articulation_to_lily(art)

        # Check for ties (if any note is tied)
        if any(n.tied for n in nr.notes):
            result += "~"

        return result

    # Single note
    return _note_to_lily(nr.notes[0], nr.dur, nr.articulations)


def _bar_rest(bar_length: int) -> str:
    """Generate a rest for an entire bar.

    Args:
        bar_length: Length of bar in ticks (1024 = whole note)

    Returns:
        LilyPond rest notation
    """
    if bar_length in DURATION_MAP:
        return f"R{DURATION_MAP[bar_length]}"

    # Common compound meters
    compound_rests = {
        768: "R2.",  # 3/4 or 6/8
        1536: "R1.",  # 6/4
        384: "R4.",  # 3/8
        1280: "R1*5/4",  # 5/4
    }
    if bar_length in compound_rests:
        return compound_rests[bar_length]

    # Default to R1 for unknown lengths
    return "R1"


def _convert_bar(
    bar: Bar, active_slurs: dict[int, bool], active_hairpins: dict[int, str]
) -> str:
    """Convert a single bar to LilyPond.

    Args:
        bar: The bar to convert
        active_slurs: Tracking dict for voice -> slur active
        active_hairpins: Tracking dict for voice -> hairpin type

    Returns:
        LilyPond string for this bar
    """
    result: list[str] = []
    has_notes = False

    for elem in bar.elements:
        match elem:
            case TimeSignature():
                result.append(_time_to_lily(elem.num, elem.den))

            case KeySignature():
                result.append(f"\\key {_key_to_lily(elem.fifths, elem.mode)}")

            case Clef():
                result.append(f"\\clef {_clef_to_lily(elem.type)}")

            case NoteRest():
                lily = _noterest_to_lily(elem)
                has_notes = True

                # Check for slur start/end
                # (This is simplified - real implementation would track by position)

                result.append(lily)

            case Dynamic():
                result.append(f"\\{elem.text}")

            case Slur():
                # Slurs are handled with ( and ) around notes
                # This is a simplified approach
                pass

            case Hairpin():
                if elem.type == "cresc":
                    result.append("\\<")
                else:
                    result.append("\\>")

            case Tuplet():
                # Tuplets wrap notes: \tuplet 3/2 { ... }
                # This would need more context to implement properly
                pass

            case Barline():
                if lily_bar := _barline_to_lily(elem.type):
                    result.append(lily_bar)

            case _:  # pragma: no cover
                raise TypeError(f"Unknown bar element type: {type(elem).__name__}")

    # If bar has no notes/rests, output a full-bar rest
    if not has_notes:
        result.append(_bar_rest(bar.length))

    return " ".join(result)


def _convert_staff(staff: Staff, bar_count: int) -> str:
    """Convert a staff to LilyPond."""
    lines: list[str] = []

    # Staff header
    lines.append(f'  \\new Staff = "{staff.instrument or f"Staff {staff.n}"}" {{')

    # Initial settings
    lines.append(f"    \\clef {_clef_to_lily(staff.clef)}")
    lines.append(f"    \\key {_key_to_lily(staff.key_sig)}")

    # Convert bars
    active_slurs: dict[int, bool] = {}
    active_hairpins: dict[int, str] = {}

    bar_contents: list[str] = []
    for bar in staff.bars:
        bar_contents.append(_convert_bar(bar, active_slurs, active_hairpins))
        bar_contents.append("|")  # Bar line

    lines.append("    " + " ".join(bar_contents))
    lines.append("  }")

    return "\n".join(lines)


def _convert_movement(movement: Movement) -> str:
    """Convert a movement to LilyPond."""
    lines: list[str] = []

    if movement.title:
        lines.append(f"% Movement {movement.n}: {movement.title}")

    lines.append("\\score {")
    lines.append("  <<")

    for staff in movement.staves:
        lines.append(_convert_staff(staff, len(staff.bars)))

    lines.append("  >>")
    lines.append("}")

    return "\n".join(lines)


def to_lilypond(score: Score) -> str:
    """Convert a Score to LilyPond format.

    Args:
        score: Parsed Mahlif Score object

    Returns:
        LilyPond source code as a string
    """
    lines: list[str] = []

    # Version header
    lines.append('\\version "2.24.0"')
    lines.append("")

    # Header block
    lines.append("\\header {")
    if score.meta.work_title:
        lines.append(f'  title = "{score.meta.work_title}"')
    if score.meta.composer:
        lines.append(f'  composer = "{score.meta.composer}"')
    if score.meta.lyricist:
        lines.append(f'  poet = "{score.meta.lyricist}"')
    if score.meta.arranger:
        lines.append(f'  arranger = "{score.meta.arranger}"')
    if score.meta.copyright:
        lines.append(f'  copyright = "{score.meta.copyright}"')
    lines.append("}")
    lines.append("")

    # Paper block for layout
    layout = (
        score.layout
        if not score.is_multi_movement
        else (score.movements[0].layout if score.movements else score.layout)
    )
    lines.append("\\paper {")
    lines.append(
        f"  #(set-paper-size '(cons (* {layout.page_width} mm) (* {layout.page_height} mm)))"
    )
    lines.append("}")
    lines.append("")

    # Score content
    if score.is_multi_movement:
        # Multi-movement work
        for movement in score.movements:
            lines.append(_convert_movement(movement))
            lines.append("")
    else:
        # Single score
        lines.append("\\score {")
        lines.append("  <<")

        for staff in score.staves:
            lines.append(_convert_staff(staff, len(staff.bars)))

        lines.append("  >>")
        lines.append("}")

    return "\n".join(lines)
