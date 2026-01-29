"""Tests for mahlif CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from mahlif.cli import detect_format
from mahlif.cli import main
from mahlif.cli import _get_version


# =============================================================================
# Format Detection
# =============================================================================


class TestDetectFormat:
    """Tests for format detection."""

    def test_mahlif_xml(self) -> None:
        """Test .mahlif.xml detection."""
        assert detect_format(Path("score.mahlif.xml")) == "mahlif"
        assert detect_format(Path("Score.MAHLIF.XML")) == "mahlif"

    def test_mahlif(self) -> None:
        """Test .mahlif detection."""
        assert detect_format(Path("score.mahlif")) == "mahlif"

    def test_sibelius(self) -> None:
        """Test .plg detection."""
        assert detect_format(Path("plugin.plg")) == "sibelius"

    def test_lilypond(self) -> None:
        """Test .ly detection."""
        assert detect_format(Path("score.ly")) == "lilypond"

    def test_musicxml(self) -> None:
        """Test .musicxml and .mxl detection."""
        assert detect_format(Path("score.musicxml")) == "musicxml"
        assert detect_format(Path("score.mxl")) == "musicxml"

    def test_pdf(self) -> None:
        """Test .pdf detection."""
        assert detect_format(Path("score.pdf")) == "pdf"

    def test_unknown(self) -> None:
        """Test unknown format."""
        assert detect_format(Path("score.txt")) is None
        assert detect_format(Path("score")) is None


# =============================================================================
# Main CLI
# =============================================================================


class TestMainCLI:
    """Tests for main CLI entry point."""

    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test running with no args shows help."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "mahlif" in captured.out

    def test_get_version(self) -> None:
        """Test _get_version returns version string."""
        version = _get_version()
        assert version  # Non-empty
        assert "." in version or version == "unknown"


# =============================================================================
# Convert Command
# =============================================================================


class TestConvertCommand:
    """Tests for convert command."""

    def test_source_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error when source file doesn't exist."""
        result = main(["convert", "/nonexistent/file.mahlif.xml", "out.plg"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_unknown_source_format(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test error for unknown source format."""
        src = tmp_path / "score.unknown"
        src.write_text("data")
        result = main(["convert", str(src), "out.plg"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Cannot detect format" in captured.out

    def test_unknown_dest_format(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test error for unknown destination format."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text('<?xml version="1.0"?><score/>')
        result = main(["convert", str(src), "out.unknown"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Cannot detect format" in captured.out

    def test_unsupported_conversion(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test error for unsupported conversion."""
        src = tmp_path / "score.musicxml"
        src.write_text('<?xml version="1.0"?><score/>')
        result = main(["convert", str(src), "out.plg"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not supported" in captured.out

    def test_mahlif_to_sibelius(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test converting mahlif to sibelius plugin."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta><work-title>Test</work-title></meta>
  <layout/>
  <staves>
    <staff n="1" instrument="Piano">
      <bars>
        <bar n="1" length="1024">
          <note-rest pos="0" dur="256" voice="1">
            <note pitch="60"/>
          </note-rest>
        </bar>
      </bars>
    </staff>
  </staves>
</mahlif>"""
        )
        dest = tmp_path / "output.plg"
        result = main(["convert", str(src), str(dest)])
        assert result == 0
        assert dest.exists()
        # Check UTF-16 BE BOM
        raw = dest.read_bytes()
        assert raw.startswith(b"\xfe\xff")

    def test_mahlif_to_lilypond(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test converting mahlif to lilypond."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta><work-title>Test</work-title></meta>
  <layout/>
  <staves>
    <staff n="1" instrument="Piano">
      <bars>
        <bar n="1" length="1024">
          <note-rest pos="0" dur="256" voice="1">
            <note pitch="60"/>
          </note-rest>
        </bar>
      </bars>
    </staff>
  </staves>
</mahlif>"""
        )
        dest = tmp_path / "output.ly"
        result = main(["convert", str(src), str(dest)])
        assert result == 0
        assert dest.exists()
        content = dest.read_text()
        assert "\\version" in content

    def test_mahlif_to_pdf_no_lilypond(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test error when lilypond not installed."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.pdf"
        with patch("shutil.which", return_value=None):
            result = main(["convert", str(src), str(dest)])
        assert result == 1
        captured = capsys.readouterr()
        assert "LilyPond not found" in captured.out

    def test_mahlif_to_pdf_success(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test successful PDF conversion."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.pdf"

        # Mock subprocess.run to simulate lilypond creating a PDF
        def mock_run(
            cmd: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            # Find the output dir from the -o arg
            for i, arg in enumerate(cmd):
                if arg == "-o" and i + 1 < len(cmd):
                    output_base = cmd[i + 1]
                    pdf_path = Path(output_base + ".pdf")
                    pdf_path.write_bytes(b"%PDF-1.4\n")
                    break
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with patch("shutil.which", return_value="/usr/bin/lilypond"):
            with patch("subprocess.run", side_effect=mock_run):
                result = main(["convert", str(src), str(dest)])

        assert result == 0
        assert dest.exists()

    def test_mahlif_to_pdf_lilypond_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test handling lilypond compilation error."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.pdf"

        def mock_run(
            cmd: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(cmd, 1, "", "error: bad syntax")

        with patch("shutil.which", return_value="/usr/bin/lilypond"):
            with patch("subprocess.run", side_effect=mock_run):
                result = main(["convert", str(src), str(dest)])

        assert result == 1
        captured = capsys.readouterr()
        assert "compilation failed" in captured.out

    def test_mahlif_to_pdf_no_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test handling lilypond not producing PDF."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.pdf"

        def mock_run(
            cmd: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            # Don't create PDF
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with patch("shutil.which", return_value="/usr/bin/lilypond"):
            with patch("subprocess.run", side_effect=mock_run):
                result = main(["convert", str(src), str(dest)])

        assert result == 1
        captured = capsys.readouterr()
        assert "did not produce PDF" in captured.out

    def test_explicit_format_flags(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test using --from and --to flags."""
        src = tmp_path / "score.xml"  # Ambiguous extension
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output"  # No extension
        result = main(
            ["convert", "--from", "mahlif", "--to", "lilypond", str(src), str(dest)]
        )
        assert result == 0
        assert dest.exists()

    def test_convert_dry_run_sibelius(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test convert --dry-run for sibelius."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.plg"
        result = main(["convert", "--dry-run", str(src), str(dest)])
        assert result == 0
        assert not dest.exists()  # File not created
        captured = capsys.readouterr()
        assert "Would convert" in captured.out

    def test_convert_dry_run_lilypond(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test convert --dry-run for lilypond."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.ly"
        result = main(["convert", "--dry-run", str(src), str(dest)])
        assert result == 0
        assert not dest.exists()

    def test_convert_dry_run_pdf(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test convert --dry-run for pdf."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        dest = tmp_path / "output.pdf"
        with patch("shutil.which", return_value="/usr/bin/lilypond"):
            result = main(["convert", "--dry-run", str(src), str(dest)])
        assert result == 0
        assert not dest.exists()
        captured = capsys.readouterr()
        assert "Would convert" in captured.out


# =============================================================================
# Stats Command
# =============================================================================


class TestStatsCommand:
    """Tests for stats command."""

    def test_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error when file doesn't exist."""
        result = main(["stats", "/nonexistent/file.mahlif.xml"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_basic_stats(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test basic statistics output."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta>
    <work-title>Test Score</work-title>
    <composer>Test Composer</composer>
  </meta>
  <layout page-width="210" page-height="297"/>
  <staves>
    <staff n="1" instrument="Piano" full-name="Piano" clef="treble">
      <bars>
        <bar n="1" length="1024">
          <note-rest pos="0" dur="256" voice="1">
            <note pitch="60"/>
          </note-rest>
          <dynamic pos="0" text="f"/>
        </bar>
      </bars>
    </staff>
  </staves>
</mahlif>"""
        )
        result = main(["stats", str(src)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Test Score" in captured.out
        assert "Test Composer" in captured.out
        assert "Staves: 1" in captured.out

    def test_json_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test JSON statistics output."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta><work-title>JSON Test</work-title></meta>
  <layout/>
  <staves/>
</mahlif>"""
        )
        result = main(["stats", "--json", str(src)])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["title"] == "JSON Test"
        assert "staves" in data
        assert "staff_stats" in data

    def test_verbose_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test verbose statistics output."""
        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves>
    <staff n="1" instrument="Violin" full-name="Violin I" clef="treble">
      <bars>
        <bar n="1" length="1024">
          <note-rest pos="0" dur="256" voice="1">
            <note pitch="60"/>
          </note-rest>
        </bar>
      </bars>
    </staff>
  </staves>
</mahlif>"""
        )
        result = main(["stats", "--verbose", str(src)])
        assert result == 0
        captured = capsys.readouterr()
        assert "=== Staves ===" in captured.out
        assert "Violin I" in captured.out


# =============================================================================
# Stats Module
# =============================================================================


class TestStatsModule:
    """Tests for stats module functions."""

    def test_compute_stats_empty_score(self) -> None:
        """Test stats computation for empty score."""
        from mahlif.models import Layout
        from mahlif.models import Meta
        from mahlif.models import Score
        from mahlif.models import SystemStaff
        from mahlif.stats import compute_stats

        score = Score(
            meta=Meta(),
            layout=Layout(),
            staves=[],
            system_staff=SystemStaff(bars=[]),
        )
        stats = compute_stats(score)
        assert stats.staves == 0
        assert stats.notes == 0

    def test_compute_stats_bar_without_notes(self) -> None:
        """Test stats computation for bar with only rests/dynamics."""
        from mahlif.models import Bar
        from mahlif.models import Dynamic
        from mahlif.models import Layout
        from mahlif.models import Meta
        from mahlif.models import NoteRest
        from mahlif.models import Score
        from mahlif.models import Staff
        from mahlif.models import SystemStaff
        from mahlif.stats import compute_stats

        score = Score(
            meta=Meta(),
            layout=Layout(),
            staves=[
                Staff(
                    n=1,
                    instrument="Piano",
                    bars=[
                        Bar(
                            n=1,
                            length=1024,
                            elements=[
                                NoteRest(pos=0, dur=256, notes=[]),  # rest only
                                Dynamic(pos=0, text="p"),
                            ],
                        ),
                    ],
                ),
            ],
            system_staff=SystemStaff(bars=[]),
        )
        stats = compute_stats(score)
        assert stats.rests == 1
        assert stats.dynamics == 1
        assert stats.notes == 0
        # Bar has no notes, so bars_with_content should be 0
        assert stats.staff_stats[0].bars_with_content == 0

    def test_compute_stats_uncounted_element_types(self) -> None:
        """Test stats computation ignores uncounted element types."""
        from mahlif.models import Bar
        from mahlif.models import Clef
        from mahlif.models import KeySignature
        from mahlif.models import Layout
        from mahlif.models import Meta
        from mahlif.models import Score
        from mahlif.models import Staff
        from mahlif.models import SystemStaff
        from mahlif.models import Tempo
        from mahlif.models import TimeSignature
        from mahlif.stats import compute_stats

        score = Score(
            meta=Meta(),
            layout=Layout(),
            staves=[
                Staff(
                    n=1,
                    instrument="Piano",
                    bars=[
                        Bar(
                            n=1,
                            length=1024,
                            elements=[
                                # These element types are not counted in stats
                                Clef(pos=0, type="treble"),
                                KeySignature(pos=0, fifths=0),
                                TimeSignature(pos=0, num=4, den=4),
                                Tempo(pos=0, text="Allegro", bpm=120),
                            ],
                        ),
                    ],
                ),
            ],
            system_staff=SystemStaff(bars=[]),
        )
        stats = compute_stats(score)
        # None of these element types are counted
        assert stats.notes == 0
        assert stats.chords == 0
        assert stats.rests == 0
        assert stats.dynamics == 0
        assert stats.slurs == 0
        assert stats.hairpins == 0
        assert stats.text == 0

    def test_compute_stats_with_elements(self) -> None:
        """Test stats computation with various elements."""
        from mahlif.models import Bar
        from mahlif.models import Dynamic
        from mahlif.models import Hairpin
        from mahlif.models import Layout
        from mahlif.models import Meta
        from mahlif.models import Note
        from mahlif.models import NoteRest
        from mahlif.models import Score
        from mahlif.models import Slur
        from mahlif.models import Staff
        from mahlif.models import SystemStaff
        from mahlif.models import Text
        from mahlif.stats import compute_stats

        score = Score(
            meta=Meta(work_title="Test", composer="Composer"),
            layout=Layout(page_width=210, page_height=297, staff_height=7),
            staves=[
                Staff(
                    n=1,
                    instrument="Piano",
                    full_name="Piano",
                    short_name="Pno.",
                    clef="bass",
                    bars=[
                        Bar(
                            n=1,
                            length=1024,
                            elements=[
                                NoteRest(
                                    pos=0,
                                    dur=256,
                                    notes=[Note(pitch=60), Note(pitch=64)],
                                ),  # chord
                                NoteRest(
                                    pos=256, dur=256, notes=[Note(pitch=62)]
                                ),  # note
                                NoteRest(pos=512, dur=256, notes=[]),  # rest
                                Dynamic(pos=0, text="f"),
                                Slur(
                                    start_bar=1,
                                    start_pos=0,
                                    end_bar=1,
                                    end_pos=512,
                                    voice=1,
                                ),
                                Hairpin(
                                    start_bar=1,
                                    start_pos=0,
                                    end_bar=1,
                                    end_pos=256,
                                    type="cresc",
                                    voice=1,
                                ),
                                Text(pos=0, text="dolce"),
                            ],
                        ),
                    ],
                ),
            ],
            system_staff=SystemStaff(bars=[]),
        )
        stats = compute_stats(score)
        assert stats.title == "Test"
        assert stats.composer == "Composer"
        assert stats.staves == 1
        assert stats.bars == 1
        assert stats.notes == 1
        assert stats.chords == 1
        assert stats.rests == 1
        assert stats.dynamics == 1
        assert stats.slurs == 1
        assert stats.hairpins == 1
        assert stats.text == 1
        assert len(stats.staff_stats) == 1
        assert stats.staff_stats[0].full_name == "Piano"

    def test_format_stats_minimal(self) -> None:
        """Test formatting minimal stats."""
        from mahlif.stats import format_stats
        from mahlif.stats import ScoreStats

        stats = ScoreStats(
            title="",
            composer="",
            source="",
            page_width=0,
            page_height=0,
            staff_height=0,
            staves=0,
            bars=0,
            notes=0,
            chords=0,
            rests=0,
            dynamics=0,
            slurs=0,
            hairpins=0,
            text=0,
            staff_stats=[],
        )
        output = format_stats(stats)
        assert "=== Meta ===" in output
        assert "=== Content ===" in output

    def test_format_stats_verbose(self) -> None:
        """Test verbose formatting."""
        from mahlif.stats import format_stats
        from mahlif.stats import ScoreStats
        from mahlif.stats import StaffStats

        stats = ScoreStats(
            title="Test",
            composer="Composer",
            source="/path/to/file",
            page_width=210,
            page_height=297,
            staff_height=7,
            staves=1,
            bars=10,
            notes=100,
            chords=50,
            rests=25,
            dynamics=10,
            slurs=5,
            hairpins=3,
            text=2,
            staff_stats=[
                StaffStats(
                    number=1,
                    full_name="Violin",
                    short_name="Vln.",
                    clef="treble",
                    bars_total=10,
                    bars_with_content=8,
                    notes=100,
                    chords=50,
                    rests=25,
                )
            ],
        )
        output = format_stats(stats, verbose=True)
        assert "=== Staves ===" in output
        assert "Violin" in output
        assert "8/10 bars with content" in output

    def test_stats_main_direct(self, tmp_path: Path) -> None:
        """Test stats module main function directly."""
        from mahlif.stats import main as stats_main

        src = tmp_path / "score.mahlif.xml"
        src.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
  <meta/>
  <layout/>
  <staves/>
</mahlif>"""
        )
        result = stats_main([str(src)])
        assert result == 0
