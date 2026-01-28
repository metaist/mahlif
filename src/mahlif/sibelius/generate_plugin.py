#!/usr/bin/env python3
"""Generate a Sibelius import plugin from Mahlif XML.

The generated .plg file contains all score data embedded as ManuScript code,
avoiding the need for slow file parsing in Sibelius.

Usage:
    python generate_plugin.py input.mahlif.xml output.plg
"""

from __future__ import annotations

import sys
from pathlib import Path

from mahlif import parse
from mahlif.models import Barline
from mahlif.models import Clef
from mahlif.models import Dynamic
from mahlif.models import Hairpin
from mahlif.models import KeySignature
from mahlif.models import NoteRest
from mahlif.models import Rehearsal
from mahlif.models import Score
from mahlif.models import Slur
from mahlif.models import Tempo
from mahlif.models import Text
from mahlif.models import TimeSignature
from mahlif.models import Tuplet


def _calc_spanner_duration(
    start_bar: int,
    start_pos: int,
    end_bar: int,
    end_pos: int,
    bar_length: int,
) -> int:
    """Calculate total duration for a spanner crossing bars."""
    if start_bar == end_bar:
        return end_pos - start_pos

    # Cross-bar: remaining in start bar + full bars + end position
    # This is approximate since bar lengths can vary
    remaining_in_start = bar_length - start_pos
    full_bars = (end_bar - start_bar - 1) * bar_length
    return remaining_in_start + full_bars + end_pos


# Articulation name -> ManuScript constant
# From ManuScript Language.pdf "Articulations" section
ARTICULATION_MAP = {
    "staccato": "StaccatoArtic",
    "accent": "AccentArtic",
    "tenuto": "TenutoArtic",
    "marcato": "MarcatoArtic",
    "staccatissimo": "StaccatissimoArtic",
    "wedge": "WedgeArtic",
    "fermata": "PauseArtic",  # Called "Pause" in ManuScript
    "pause": "PauseArtic",
    "up-bow": "UpBowArtic",
    "down-bow": "DownBowArtic",
    "harmonic": "HarmonicArtic",
    "plus": "PlusArtic",
    "tri-pause": "TriPauseArtic",
    "square-pause": "SquarePauseArtic",
}


def escape_str(text: str) -> str:
    """Escape string for ManuScript."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def generate_plugin(score: Score, title: str = "Imported Score") -> str:
    """Generate a ManuScript plugin from a Score."""
    lines: list[str] = []

    # Header
    lines.append("{")
    lines.append('\tInitialize "() {')
    lines.append(f"AddToPluginsMenu('Mahlif: Import {escape_str(title)}', 'Run');")
    lines.append('}"')
    lines.append('\tRun "() {')
    lines.append("score = Sibelius.ActiveScore;")
    lines.append("if (null = score) {")
    lines.append("\tSibelius.MessageBox('No score open. Create a blank score first.');")
    lines.append("\treturn False;")
    lines.append("}")
    lines.append("")

    # Count existing staves
    lines.append("existingCount = 0;")
    lines.append("for each s in score {")
    lines.append("\texistingCount = existingCount + 1;")
    lines.append("}")
    lines.append("")

    # Add bars if needed
    max_bars = max((len(s.bars) for s in score.staves), default=0)
    lines.append(f"// Ensure we have {max_bars} bars")
    lines.append(f"barsNeeded = {max_bars} - score.SystemStaff.BarCount;")
    lines.append("if (barsNeeded > 0) {")
    lines.append("\tscore.AddBars(barsNeeded);")
    lines.append("}")
    lines.append("")

    # Create instruments
    for staff in score.staves:
        instrument = staff.instrument or f"Staff {staff.n}"
        lines.append(f"score.CreateInstrument('{escape_str(instrument)}');")

    lines.append("")

    # Get staff references into array (skip existing staves)
    lines.append("staves = CreateSparseArray();")
    lines.append("idx = 0;")
    lines.append("staffNum = 0;")
    lines.append("for each s in score {")
    lines.append("\tif (staffNum >= existingCount) {")
    lines.append("\t\tstaves[idx] = s;")
    lines.append("\t\tidx = idx + 1;")
    lines.append("\t}")
    lines.append("\tstaffNum = staffNum + 1;")
    lines.append("}")
    lines.append("")

    # Page layout
    if score.layout.page_width > 0 or score.layout.page_height > 0:
        lines.append("// Page layout")
        lines.append("docSetup = score.DocumentSetup;")
        lines.append("docSetup.Units = 'mm';")
        if score.layout.page_width > 0:
            lines.append(f"docSetup.PageWidth = {score.layout.page_width};")
        if score.layout.page_height > 0:
            lines.append(f"docSetup.PageHeight = {score.layout.page_height};")
        if score.layout.staff_height > 0:
            lines.append(f"docSetup.StaffSize = {score.layout.staff_height};")
        lines.append("")

    # Progress dialog
    lines.append("Sibelius.CreateProgressDialog('Importing...', 0, 100);")
    lines.append("")

    total_staves = len(score.staves)
    # Add notes to each staff
    for staff_idx, staff in enumerate(score.staves):
        pct = int((staff_idx * 100) / total_staves)
        lines.append(
            f"Sibelius.UpdateProgressDialog({pct}, 'Staff {staff_idx + 1} of {total_staves}...');"
        )
        lines.append(f"// Staff {staff_idx + 1}: {staff.instrument or 'unnamed'}")
        lines.append(f"st = staves[{staff_idx}];")
        lines.append("if (st = null) {")
        lines.append(f"\tSibelius.MessageBox('Staff {staff_idx} is null');")
        lines.append("\treturn False;")
        lines.append("}")

        for bar in staff.bars:
            has_notes = any(
                isinstance(e, NoteRest) and not e.is_rest for e in bar.elements
            )
            if not has_notes:
                continue

            lines.append(f"b = st.NthBar({bar.n});")

            # Handle page/system breaks
            if bar.break_type:
                break_map = {
                    "page": "EndOfPage",
                    "system": "EndOfSystem",
                }
                if bar.break_type in break_map:
                    lines.append(f"b.BreakType = {break_map[bar.break_type]};")

            for elem in bar.elements:
                if isinstance(elem, NoteRest) and not elem.is_rest:
                    if elem.is_chord:
                        # First note
                        note = elem.notes[0]
                        tied = "True" if note.tied else "False"
                        lines.append(
                            f"nr = b.AddNote({elem.pos}, {note.pitch}, "
                            f"{elem.dur}, {tied}, {elem.voice});"
                        )
                        # Additional notes (only if nr is valid)
                        lines.append("if (nr != null) {")
                        for note in elem.notes[1:]:
                            lines.append(f"\tnr.AddNote({note.pitch});")
                        # Articulations
                        for artic in elem.articulations:
                            if artic in ARTICULATION_MAP:
                                lines.append(
                                    f"\tnr.SetArticulation({ARTICULATION_MAP[artic]}, True);"
                                )
                        # dx/dy offsets
                        if elem.offset.dx != 0:
                            lines.append(f"\tnr.Dx = {int(elem.offset.dx)};")
                        if elem.offset.dy != 0:
                            lines.append(f"\tnr.Dy = {int(elem.offset.dy)};")
                        # Stem direction
                        if elem.stem == "up":
                            lines.append("\tnr.StemDirection = 1;")
                        elif elem.stem == "down":
                            lines.append("\tnr.StemDirection = -1;")
                        lines.append("}")
                    else:
                        # Single note
                        note = elem.notes[0]
                        tied = "True" if note.tied else "False"
                        lines.append(
                            f"nr = b.AddNote({elem.pos}, {note.pitch}, "
                            f"{elem.dur}, {tied}, {elem.voice});"
                        )
                        # Articulations, offsets, stem
                        has_extras = (
                            elem.articulations
                            or elem.offset.dx != 0
                            or elem.offset.dy != 0
                            or elem.stem in ("up", "down")
                        )
                        if has_extras:
                            lines.append("if (nr != null) {")
                            for artic in elem.articulations:
                                if artic in ARTICULATION_MAP:
                                    lines.append(
                                        f"\tnr.SetArticulation({ARTICULATION_MAP[artic]}, True);"
                                    )
                            if elem.offset.dx != 0:
                                lines.append(f"\tnr.Dx = {int(elem.offset.dx)};")
                            if elem.offset.dy != 0:
                                lines.append(f"\tnr.Dy = {int(elem.offset.dy)};")
                            if elem.stem == "up":
                                lines.append("\tnr.StemDirection = 1;")
                            elif elem.stem == "down":
                                lines.append("\tnr.StemDirection = -1;")
                            lines.append("}")

                elif isinstance(elem, Dynamic):
                    # Dynamics use expression text style
                    lines.append(
                        f"b.AddText({elem.pos}, '{escape_str(elem.text)}', "
                        f"'text.staff.expression');"
                    )

                elif isinstance(elem, Text):
                    # Generic text - try to map style
                    style = "text.staff.plain"
                    if "technique" in (elem.style or ""):
                        style = "text.staff.technique"
                    elif "expression" in (elem.style or ""):
                        style = "text.staff.expression"
                    lines.append(
                        f"b.AddText({elem.pos}, '{escape_str(elem.text)}', '{style}');"
                    )

                elif isinstance(elem, Clef):
                    # Map clef type to style ID
                    clef_map = {
                        "treble": "clef.treble",
                        "bass": "clef.bass",
                        "alto": "clef.alto",
                        "tenor": "clef.tenor",
                        "percussion": "clef.percussion",
                    }
                    clef_style = clef_map.get(elem.type, "clef.treble")
                    lines.append(f"b.AddClef({elem.pos}, '{clef_style}');")

                elif isinstance(elem, Slur):
                    # Slurs span from start to end position
                    # AddLine(pos, duration, style)
                    duration = _calc_spanner_duration(
                        elem.start_bar,
                        elem.start_pos,
                        elem.end_bar,
                        elem.end_pos,
                        bar.length,
                    )
                    if duration > 0:
                        lines.append(
                            f"b.AddLine({elem.start_pos}, {duration}, "
                            f"'line.staff.slur.up', 0, 0, {elem.voice});"
                        )

                elif isinstance(elem, Hairpin):
                    # Hairpins: crescendo or diminuendo
                    duration = _calc_spanner_duration(
                        elem.start_bar,
                        elem.start_pos,
                        elem.end_bar,
                        elem.end_pos,
                        bar.length,
                    )
                    if duration > 0:
                        style = (
                            "line.staff.hairpin.crescendo"
                            if elem.type == "cresc"
                            else "line.staff.hairpin.diminuendo"
                        )
                        lines.append(
                            f"b.AddLine({elem.start_pos}, {duration}, "
                            f"'{style}', 0, 0, {elem.voice});"
                        )

                elif isinstance(elem, Tuplet):
                    # AddTuplet(pos, voice, left, right, unit)
                    # left/right = ratio (e.g., 3:2 triplet)
                    # unit = duration of each note in the tuplet
                    lines.append(
                        f"b.AddTuplet({elem.start_pos}, 1, {elem.num}, {elem.den}, 256);"
                    )

                elif isinstance(elem, Barline):
                    # Special barlines (repeat, double, final)
                    barline_map = {
                        "double": "DoubleBarline",
                        "final": "FinalBarline",
                        "repeat-start": "StartRepeatBarline",
                        "repeat-end": "EndRepeatBarline",
                        "dashed": "DashedBarline",
                    }
                    if elem.type in barline_map:
                        lines.append(f"b.AddSpecialBarline({barline_map[elem.type]});")

                elif isinstance(elem, Tempo):
                    # Tempo markings with metronome
                    if elem.text:
                        lines.append(
                            f"b.AddText({elem.pos}, '{escape_str(elem.text)}', "
                            f"'text.system.tempo');"
                        )

                elif isinstance(elem, Rehearsal):
                    # Rehearsal marks
                    lines.append(
                        f"b.AddText({elem.pos}, '{escape_str(elem.text)}', "
                        f"'text.system.rehearsalmark');"
                    )

        # Add lyrics for this staff (lyrics are at staff level, not bar level)
        for lyrics in staff.lyrics:
            lines.append(f"// Lyrics voice {lyrics.voice} verse {lyrics.verse}")
            for syl in lyrics.syllables:
                if syl.bar is None:
                    continue
                # AddLyric(pos, dur, text, syllable_type, num_notes, voice)
                # syllable_type: 0=end, 1=middle, 2=start
                syl_type = 1 if syl.hyphen else 0  # middle or end
                lines.append(f"b = st.NthBar({syl.bar});")
                lines.append(
                    f"b.AddLyric({syl.pos}, 256, '{escape_str(syl.text)}', "
                    f"{syl_type}, 1, {lyrics.voice});"
                )

        lines.append("")

    # Add time/key signatures from system staff
    if score.system_staff.bars:
        lines.append("// System staff: time/key signatures")
        for bar in score.system_staff.bars:
            has_time_or_key = any(
                isinstance(e, (TimeSignature, KeySignature)) for e in bar.elements
            )
            if not has_time_or_key:
                continue

            lines.append(f"sysBar = score.SystemStaff.NthBar({bar.n});")
            for elem in bar.elements:
                if isinstance(elem, TimeSignature):
                    # AddTimeSignature(top, bottom, cautionary, rewrite)
                    lines.append(
                        f"sysBar.AddTimeSignature({elem.num}, {elem.den}, False, False);"
                    )
                elif isinstance(elem, KeySignature):
                    # AddKeySignature(pos, sharps, major)
                    is_major = "True" if elem.mode == "major" else "False"
                    lines.append(
                        f"sysBar.AddKeySignature({elem.pos}, {elem.fifths}, {is_major});"
                    )
        lines.append("")

    # Footer
    lines.append("Sibelius.DestroyProgressDialog();")
    lines.append(f"Sibelius.MessageBox('Import complete: {len(score.staves)} staves');")
    lines.append("return True;")
    lines.append('}"')
    lines.append("}")

    return "\n".join(lines)


def convert_to_utf16(source: Path, dest: Path) -> None:
    """Convert UTF-8 plugin to UTF-16 BE with BOM."""
    content = source.read_text(encoding="utf-8")
    with open(dest, "wb") as f:
        f.write(b"\xfe\xff")
        f.write(content.encode("utf-16-be"))


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.mahlif.xml> <output.plg>")
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return 1

    print(f"Parsing {input_path}...")
    score = parse(input_path)

    title = score.meta.work_title or input_path.stem
    print(f"Generating plugin for '{title}'...")
    print(f"  {len(score.staves)} staves")

    total_notes = sum(
        1
        for staff in score.staves
        for bar in staff.bars
        for elem in bar.elements
        if isinstance(elem, NoteRest) and not elem.is_rest
    )
    print(f"  {total_notes} notes/chords")

    plugin_source = generate_plugin(score, title)

    # Write UTF-8 temp, convert to UTF-16
    utf8_path = output_path.with_suffix(".utf8.tmp")
    utf8_path.write_text(plugin_source, encoding="utf-8")
    convert_to_utf16(utf8_path, output_path)
    utf8_path.unlink()

    print(f"Generated {output_path}")
    print(f"  {output_path.stat().st_size:,} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
