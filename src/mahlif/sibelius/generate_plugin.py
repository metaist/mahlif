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
from mahlif.models import Clef
from mahlif.models import Dynamic
from mahlif.models import Hairpin
from mahlif.models import KeySignature
from mahlif.models import NoteRest
from mahlif.models import Score
from mahlif.models import Slur
from mahlif.models import Text
from mahlif.models import TimeSignature


def escape_str(text: str) -> str:
    """Escape string for ManuScript."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def generate_plugin(score: Score, title: str = "Imported Score") -> str:
    """Generate a ManuScript plugin from a Score."""
    lines: list[str] = []

    # Header
    lines.append("{")
    lines.append('\tInitialize "() {')
    lines.append(f"AddToPluginsMenu('Import: {escape_str(title)}', 'Run');")
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
                        lines.append("}")
                    else:
                        # Single note
                        note = elem.notes[0]
                        tied = "True" if note.tied else "False"
                        lines.append(
                            f"b.AddNote({elem.pos}, {note.pitch}, "
                            f"{elem.dur}, {tied}, {elem.voice});"
                        )

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
                    # Calculate duration based on end position
                    # For cross-bar slurs, we need the total duration
                    if elem.start_bar == elem.end_bar:
                        duration = elem.end_pos - elem.start_pos
                        if duration > 0:
                            lines.append(
                                f"b.AddLine({elem.start_pos}, {duration}, "
                                f"'line.staff.slur.up', 0, 0, {elem.voice});"
                            )
                    # Cross-bar slurs need special handling (skip for now)

                elif isinstance(elem, Hairpin):
                    # Hairpins: crescendo or diminuendo
                    if elem.start_bar == elem.end_bar:
                        duration = elem.end_pos - elem.start_pos
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
