"""Statistics and inspection for Mahlif XML files.

Usage:
    mahlif stats score.mahlif.xml
    mahlif stats --json score.mahlif.xml
    mahlif stats --verbose score.mahlif.xml
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from mahlif import parse
from mahlif.models import Dynamic
from mahlif.models import Hairpin
from mahlif.models import NoteRest
from mahlif.models import Score
from mahlif.models import Slur
from mahlif.models import Text


@dataclass
class StaffStats:
    """Statistics for a single staff."""

    number: int
    full_name: str
    short_name: str
    clef: str
    bars_total: int
    bars_with_content: int
    notes: int
    chords: int
    rests: int


@dataclass
class ScoreStats:
    """Statistics for an entire score."""

    # Meta
    title: str
    composer: str
    source: str

    # Layout
    page_width: float
    page_height: float
    staff_height: float

    # Content totals
    staves: int
    bars: int
    notes: int
    chords: int
    rests: int
    dynamics: int
    slurs: int
    hairpins: int
    text: int

    # Per-staff breakdown
    staff_stats: list[StaffStats] = field(default_factory=list)


def compute_stats(score: Score) -> ScoreStats:
    """Compute statistics for a score.

    Args:
        score: Parsed score

    Returns:
        ScoreStats with all computed values
    """
    total_notes = 0
    total_chords = 0
    total_rests = 0
    total_dynamics = 0
    total_slurs = 0
    total_hairpins = 0
    total_text = 0
    max_bars = 0

    staff_stats: list[StaffStats] = []

    for staff in score.staves:
        staff_notes = 0
        staff_chords = 0
        staff_rests = 0
        bars_with_content = 0

        for bar in staff.bars:
            bar_has_notes = False
            for elem in bar.elements:
                match elem:
                    case NoteRest() if elem.is_rest:
                        staff_rests += 1
                    case NoteRest() if elem.is_chord:
                        staff_chords += 1
                        bar_has_notes = True
                    case NoteRest():
                        staff_notes += 1
                        bar_has_notes = True
                    case Dynamic():
                        total_dynamics += 1
                    case Slur():
                        total_slurs += 1
                    case Hairpin():
                        total_hairpins += 1
                    case Text():
                        total_text += 1
                    case _:
                        pass  # Other element types not counted in stats

            if bar_has_notes:
                bars_with_content += 1

        total_notes += staff_notes
        total_chords += staff_chords
        total_rests += staff_rests
        max_bars = max(max_bars, len(staff.bars))

        staff_stats.append(
            StaffStats(
                number=staff.n,
                full_name=staff.full_name or staff.instrument or f"Staff {staff.n}",
                short_name=staff.short_name or staff.instrument_short or "",
                clef=staff.clef,
                bars_total=len(staff.bars),
                bars_with_content=bars_with_content,
                notes=staff_notes,
                chords=staff_chords,
                rests=staff_rests,
            )
        )

    return ScoreStats(
        title=score.meta.work_title or "",
        composer=score.meta.composer or "",
        source=score.meta.source_file or "",
        page_width=score.layout.page_width,
        page_height=score.layout.page_height,
        staff_height=score.layout.staff_height,
        staves=len(score.staves),
        bars=max_bars,
        notes=total_notes,
        chords=total_chords,
        rests=total_rests,
        dynamics=total_dynamics,
        slurs=total_slurs,
        hairpins=total_hairpins,
        text=total_text,
        staff_stats=staff_stats,
    )


def format_stats(stats: ScoreStats, verbose: bool = False) -> str:
    """Format statistics for display.

    Args:
        stats: Computed statistics
        verbose: Include per-staff breakdown

    Returns:
        Formatted string
    """
    lines: list[str] = []

    # Meta section
    lines.append("=== Meta ===")
    if stats.title:
        lines.append(f'Title: "{stats.title}"')
    if stats.composer:
        lines.append(f'Composer: "{stats.composer}"')
    if stats.source:
        lines.append(f"Source: {stats.source}")
    lines.append("")

    # Layout section
    lines.append("=== Layout ===")
    if stats.page_width > 0 or stats.page_height > 0:
        lines.append(f"Page: {stats.page_width} x {stats.page_height} mm")
    if stats.staff_height > 0:
        lines.append(f"Staff height: {stats.staff_height}")
    lines.append("")

    # Content section
    lines.append("=== Content ===")
    lines.append(f"Staves: {stats.staves}")
    lines.append(f"Bars: {stats.bars}")
    lines.append(f"Notes: {stats.notes:,}")
    lines.append(f"Chords: {stats.chords:,}")
    lines.append(f"Rests: {stats.rests:,}")
    lines.append(f"Dynamics: {stats.dynamics:,}")
    lines.append(f"Slurs: {stats.slurs:,}")
    lines.append(f"Hairpins: {stats.hairpins:,}")
    lines.append(f"Text: {stats.text:,}")
    lines.append("")

    # Per-staff breakdown
    if verbose and stats.staff_stats:
        lines.append("=== Staves ===")
        for ss in stats.staff_stats:
            content = f"{ss.bars_with_content}/{ss.bars_total} bars with content"
            lines.append(f"{ss.number}. {ss.full_name} ({ss.clef}): {content}")

    return "\n".join(lines)


def main(args: list[str] | None = None) -> int:
    """Main entry point for stats command.

    Args:
        args: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Show statistics for a Mahlif XML file"
    )
    parser.add_argument("file", type=Path, help="Mahlif XML file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show per-staff breakdown",
    )

    parsed = parser.parse_args(args)

    if not parsed.file.exists():
        print(f"Error: {parsed.file} not found")
        return 1

    score = parse(parsed.file)
    stats = compute_stats(score)

    if parsed.json:
        print(json.dumps(asdict(stats), indent=2))
    else:
        print(format_stats(stats, verbose=parsed.verbose))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
