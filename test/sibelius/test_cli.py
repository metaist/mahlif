"""Tests for Sibelius CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mahlif.sibelius.build import build_plugins
from mahlif.sibelius.build import convert_to_utf16be
from mahlif.sibelius.build import find_plugin_sources
from mahlif.sibelius.build import get_sibelius_plugin_dir
from mahlif.sibelius.build import main as build_main
from mahlif.sibelius.build import resolve_plugins
from mahlif.sibelius.cli import main as sibelius_main
from mahlif.sibelius.lint import fix_trailing_whitespace


# =============================================================================
# Build Module
# =============================================================================


class TestBuildModule:
    """Tests for build module."""

    def test_convert_to_utf16be(self) -> None:
        """Test UTF-16 BE conversion."""
        content = "Hello\nWorld"
        result = convert_to_utf16be(content)
        # Check BOM
        assert result[:2] == b"\xfe\xff"
        # Check content
        decoded = result[2:].decode("utf-16-be")
        assert decoded == "Hello\nWorld"

    def test_convert_to_utf16be_strips_trailing_whitespace(self) -> None:
        """Test that trailing whitespace is stripped."""
        content = "Line 1   \nLine 2\t\nLine 3"
        result = convert_to_utf16be(content)
        decoded = result[2:].decode("utf-16-be")
        assert decoded == "Line 1\nLine 2\nLine 3"

    def test_find_plugin_sources(self, tmp_path: Path) -> None:
        """Test finding plugin source files."""
        # Create some plugins
        (tmp_path / "main.plg").write_text("{}")
        (tmp_path / "other.plg").write_text("{}")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "sub.plg").write_text("{}")
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "hidden.plg").write_text("{}")

        plugins = find_plugin_sources(tmp_path)
        names = [p.name for p in plugins]

        assert "main.plg" in names
        assert "other.plg" in names
        assert "sub.plg" in names
        # Hidden directory should be excluded
        assert "hidden.plg" not in names

    def test_find_plugin_sources_empty(self, tmp_path: Path) -> None:
        """Test finding plugins in empty directory."""
        plugins = find_plugin_sources(tmp_path)
        assert plugins == []

    def test_resolve_plugins_empty(self, tmp_path: Path) -> None:
        """Test resolve_plugins with empty list returns all."""
        (tmp_path / "a.plg").write_text("{}")
        (tmp_path / "b.plg").write_text("{}")
        resolved, unresolved = resolve_plugins(tmp_path, [])
        assert len(resolved) == 2
        assert unresolved == []

    def test_resolve_plugins_by_name(self, tmp_path: Path) -> None:
        """Test resolve_plugins by name."""
        (tmp_path / "a.plg").write_text("{}")
        (tmp_path / "b.plg").write_text("{}")
        (tmp_path / "c.plg").write_text("{}")
        resolved, unresolved = resolve_plugins(tmp_path, ["a", "c"])
        assert len(resolved) == 2
        names = [p.stem for p in resolved]
        assert "a" in names
        assert "c" in names
        assert unresolved == []

    def test_resolve_plugins_by_path(self, tmp_path: Path) -> None:
        """Test resolve_plugins by path."""
        plg = tmp_path / "test.plg"
        plg.write_text("{}")
        resolved, unresolved = resolve_plugins(tmp_path, [str(plg)])
        assert len(resolved) == 1
        assert resolved[0] == plg
        assert unresolved == []

    def test_resolve_plugins_mixed(self, tmp_path: Path) -> None:
        """Test resolve_plugins with names and paths."""
        (tmp_path / "a.plg").write_text("{}")
        external = tmp_path / "external" / "b.plg"
        external.parent.mkdir()
        external.write_text("{}")

        resolved, unresolved = resolve_plugins(tmp_path, ["a", str(external)])
        assert len(resolved) == 2
        assert unresolved == []

    def test_resolve_plugins_unresolved(self, tmp_path: Path) -> None:
        """Test resolve_plugins with unresolved names."""
        (tmp_path / "a.plg").write_text("{}")
        resolved, unresolved = resolve_plugins(tmp_path, ["a", "nonexistent"])
        assert len(resolved) == 1
        assert unresolved == ["nonexistent"]

    def test_resolve_plugins_path_not_found(self, tmp_path: Path) -> None:
        """Test resolve_plugins with non-existent path."""
        resolved, unresolved = resolve_plugins(tmp_path, ["./nonexistent.plg"])
        assert resolved == []
        assert unresolved == ["./nonexistent.plg"]

    def test_build_plugins_no_source(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with no plugins found."""
        error_count, built = build_plugins(source_dir=tmp_path)
        assert error_count == 0
        assert built == []
        captured = capsys.readouterr()
        assert "No .plg files found" in captured.out

    def test_build_plugins_unresolved(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with unresolved plugins."""
        (tmp_path / "a.plg").write_text("{}")
        error_count, built = build_plugins(
            source_dir=tmp_path, plugin_names=["nonexistent"]
        )
        assert error_count == 1
        assert built == []
        captured = capsys.readouterr()
        assert "Could not find plugins" in captured.out
        assert "Available:" in captured.out

    def test_build_plugins_lint_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build fails on lint errors."""
        # Plugin without closing brace
        (tmp_path / "bad.plg").write_text("{ Initialize")
        error_count, built = build_plugins(source_dir=tmp_path)
        assert error_count == 1
        assert built == []
        captured = capsys.readouterr()
        assert "Lint errors found" in captured.out

    def test_build_plugins_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test successful plugin build."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        # Valid plugin
        (source_dir / "test.plg").write_text(
            """{
    Initialize "() {
        AddToPluginsMenu('Test', 'Run');
    }"
    Run "() {
        Sibelius.MessageBox('Hello');
    }"
}"""
        )

        error_count, built = build_plugins(source_dir=source_dir, output_dir=output_dir)
        assert error_count == 0
        assert len(built) == 1
        assert built[0].name == "test.plg"

        # Check output is UTF-16 BE
        raw = built[0].read_bytes()
        assert raw.startswith(b"\xfe\xff")

    def test_build_plugins_dry_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with dry run."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        error_count, built = build_plugins(
            source_dir=source_dir, output_dir=output_dir, dry_run=True
        )
        assert error_count == 0
        assert len(built) == 1
        # Output file should NOT exist
        assert not (output_dir / "test.plg").exists()
        captured = capsys.readouterr()
        assert "Dry run" in captured.out
        assert "Would build" in captured.out

    def test_build_plugins_specific(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test building specific plugins."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        valid_plugin = """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        (source_dir / "a.plg").write_text(valid_plugin)
        (source_dir / "b.plg").write_text(valid_plugin)
        (source_dir / "c.plg").write_text(valid_plugin)

        error_count, built = build_plugins(
            source_dir=source_dir, output_dir=output_dir, plugin_names=["a", "c"]
        )
        assert error_count == 0
        assert len(built) == 2
        names = [p.stem for p in built]
        assert "a" in names
        assert "c" in names
        assert "b" not in names

    def test_build_plugins_install(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with --install option."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        sibelius_dir = tmp_path / "sibelius"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            error_count, built = build_plugins(source_dir=source_dir, install=True)

        assert error_count == 0
        assert len(built) == 1
        # Should be in sibelius dir, not dist
        assert built[0].parent == sibelius_dir
        assert (sibelius_dir / "test.plg").exists()

    def test_build_plugins_install_no_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build --install fails when Sibelius dir not detected."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()

        (source_dir / "test.plg").write_text("{}")

        with patch("mahlif.sibelius.build.get_sibelius_plugin_dir", return_value=None):
            error_count, built = build_plugins(source_dir=source_dir, install=True)

        assert error_count == 1
        assert built == []
        captured = capsys.readouterr()
        assert "Could not detect" in captured.out

    def test_build_plugins_hardlink(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with hardlink option."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"
        sibelius_dir = tmp_path / "sibelius"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { Sibelius.MessageBox('Hello'); }"
}"""
        )

        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            error_count, built = build_plugins(
                source_dir=source_dir, output_dir=output_dir, hardlink=True
            )

        assert error_count == 0
        assert len(built) == 1

        # Check hardlink was created
        link_path = sibelius_dir / "test.plg"
        assert link_path.exists()
        # Verify it's a hardlink (same inode)
        assert link_path.stat().st_ino == built[0].stat().st_ino

    def test_build_plugins_hardlink_dry_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with hardlink and dry run."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"
        sibelius_dir = tmp_path / "sibelius"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            error_count, built = build_plugins(
                source_dir=source_dir,
                output_dir=output_dir,
                hardlink=True,
                dry_run=True,
            )

        assert error_count == 0
        # Files should NOT exist
        assert not (output_dir / "test.plg").exists()
        assert not (sibelius_dir / "test.plg").exists()

    def test_build_plugins_hardlink_quiet(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with hardlink and quiet mode."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"
        sibelius_dir = tmp_path / "sibelius"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            error_count, built = build_plugins(
                source_dir=source_dir,
                output_dir=output_dir,
                hardlink=True,
                verbose=False,
            )

        assert error_count == 0
        # Files should exist
        assert (output_dir / "test.plg").exists()
        assert (sibelius_dir / "test.plg").exists()
        # No output
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_build_plugins_hardlink_no_sibelius_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with hardlink when Sibelius dir not detected."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        with patch("mahlif.sibelius.build.get_sibelius_plugin_dir", return_value=None):
            error_count, built = build_plugins(
                source_dir=source_dir, output_dir=output_dir, hardlink=True
            )

        assert error_count == 0
        captured = capsys.readouterr()
        assert "Could not detect" in captured.out
        assert "Hardlinks not created" in captured.out

    def test_build_plugins_hardlink_overwrites(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with hardlink overwrites existing files."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"
        sibelius_dir = tmp_path / "sibelius"
        sibelius_dir.mkdir()

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        # Create existing file in sibelius dir
        (sibelius_dir / "test.plg").write_text("old content")

        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            error_count, built = build_plugins(
                source_dir=source_dir, output_dir=output_dir, hardlink=True
            )

        assert error_count == 0
        # Should be overwritten with new content
        assert (sibelius_dir / "test.plg").read_bytes().startswith(b"\xfe\xff")

    def test_build_main(self, tmp_path: Path) -> None:
        """Test build main function."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { Sibelius.MessageBox('Hello'); }"
}"""
        )

        result = build_main(["--source", str(source_dir), "-o", str(output_dir), "-q"])
        assert result == 0
        assert (output_dir / "test.plg").exists()

    def test_build_main_with_plugins(self, tmp_path: Path) -> None:
        """Test build main with specific plugins."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        valid_plugin = """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        (source_dir / "a.plg").write_text(valid_plugin)
        (source_dir / "b.plg").write_text(valid_plugin)

        result = build_main(
            ["a", "--source", str(source_dir), "-o", str(output_dir), "-q"]
        )
        assert result == 0
        assert (output_dir / "a.plg").exists()
        assert not (output_dir / "b.plg").exists()

    def test_build_plugins_quiet_no_source(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with quiet mode and no source."""
        error_count, built = build_plugins(source_dir=tmp_path, verbose=False)
        assert error_count == 0
        assert built == []
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_build_plugins_quiet_unresolved(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with quiet mode and unresolved plugins."""
        (tmp_path / "a.plg").write_text("{}")
        error_count, built = build_plugins(
            source_dir=tmp_path, plugin_names=["nonexistent"], verbose=False
        )
        assert error_count == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_build_plugins_quiet_lint_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with quiet mode and lint errors."""
        (tmp_path / "bad.plg").write_text("{ Initialize")
        error_count, built = build_plugins(source_dir=tmp_path, verbose=False)
        assert error_count == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_build_plugins_quiet_install_no_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build --install quiet mode when Sibelius dir not detected."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        (source_dir / "test.plg").write_text("{}")

        with patch("mahlif.sibelius.build.get_sibelius_plugin_dir", return_value=None):
            error_count, built = build_plugins(
                source_dir=source_dir, install=True, verbose=False
            )

        assert error_count == 1
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_build_plugins_quiet_hardlink_no_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with quiet mode, hardlink, but no Sibelius dir."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        with patch("mahlif.sibelius.build.get_sibelius_plugin_dir", return_value=None):
            error_count, built = build_plugins(
                source_dir=source_dir,
                output_dir=output_dir,
                hardlink=True,
                verbose=False,
            )

        assert error_count == 0
        # No warning output in quiet mode
        captured = capsys.readouterr()
        # Only silent warnings, no progress
        assert "Linting" not in captured.out

    def test_build_plugins_default_source(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with default source_dir (package directory)."""
        output_dir = tmp_path / "dist"
        # Don't pass source_dir - uses package default
        error_count, built = build_plugins(output_dir=output_dir)
        # Should find and build the package plugins
        assert error_count == 0
        assert len(built) > 0
        assert any("MahlifExport" in str(p) for p in built)

    def test_build_plugins_install_with_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with --install and explicit output_dir."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "custom_output"
        sibelius_dir = tmp_path / "sibelius"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            error_count, built = build_plugins(
                source_dir=source_dir,
                output_dir=output_dir,  # Explicit output overrides install default
                install=True,
            )

        assert error_count == 0
        # Should use explicit output_dir, not sibelius_dir
        assert built[0].parent == output_dir

    def test_build_plugins_unresolved_no_available(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test build with unresolved plugins and no available plugins."""
        # Empty source dir
        error_count, built = build_plugins(
            source_dir=tmp_path, plugin_names=["nonexistent"]
        )
        assert error_count == 1
        captured = capsys.readouterr()
        assert "Could not find plugins" in captured.out
        # No "Available:" line since there are no plugins
        assert "Available:" not in captured.out


# =============================================================================
# Get Plugin Dir
# =============================================================================


class TestGetPluginDir:
    """Tests for get_sibelius_plugin_dir."""

    def test_macos(self) -> None:
        """Test macOS plugin directory."""
        with patch.object(sys, "platform", "darwin"):
            result = get_sibelius_plugin_dir()
            assert result is not None
            assert "Library/Application Support/Avid/Sibelius" in str(result)

    def test_windows(self) -> None:
        """Test Windows plugin directory."""
        with patch.object(sys, "platform", "win32"):
            result = get_sibelius_plugin_dir()
            assert result is not None
            assert "Avid/Sibelius" in str(result) or "Avid\\Sibelius" in str(result)

    def test_linux(self) -> None:
        """Test Linux returns None."""
        with patch.object(sys, "platform", "linux"):
            result = get_sibelius_plugin_dir()
            assert result is None


# =============================================================================
# Lint Fix
# =============================================================================


class TestLintFix:
    """Tests for lint --fix functionality."""

    def test_fix_trailing_whitespace_utf8(self, tmp_path: Path) -> None:
        """Test fixing trailing whitespace in UTF-8 file."""
        plg = tmp_path / "test.plg"
        plg.write_text("Line 1   \nLine 2\t\nLine 3", encoding="utf-8")

        changed = fix_trailing_whitespace(plg)
        assert changed

        content = plg.read_text(encoding="utf-8")
        assert content == "Line 1\nLine 2\nLine 3"

    def test_fix_trailing_whitespace_utf16be(self, tmp_path: Path) -> None:
        """Test fixing trailing whitespace in UTF-16 BE file."""
        plg = tmp_path / "test.plg"
        content = "Line 1   \nLine 2"
        with open(plg, "wb") as f:
            f.write(b"\xfe\xff")
            f.write(content.encode("utf-16-be"))

        changed = fix_trailing_whitespace(plg)
        assert changed

        raw = plg.read_bytes()
        assert raw.startswith(b"\xfe\xff")
        decoded = raw[2:].decode("utf-16-be")
        assert decoded == "Line 1\nLine 2"

    def test_fix_trailing_whitespace_utf16le(self, tmp_path: Path) -> None:
        """Test fixing trailing whitespace in UTF-16 LE file."""
        plg = tmp_path / "test.plg"
        content = "Line 1   \nLine 2"
        with open(plg, "wb") as f:
            f.write(b"\xff\xfe")
            f.write(content.encode("utf-16-le"))

        changed = fix_trailing_whitespace(plg)
        assert changed

        raw = plg.read_bytes()
        assert raw.startswith(b"\xff\xfe")
        decoded = raw[2:].decode("utf-16-le")
        assert decoded == "Line 1\nLine 2"

    def test_fix_trailing_whitespace_no_change(self, tmp_path: Path) -> None:
        """Test no change when no trailing whitespace."""
        plg = tmp_path / "test.plg"
        plg.write_text("Line 1\nLine 2", encoding="utf-8")

        changed = fix_trailing_whitespace(plg)
        assert not changed

    def test_read_plugin_utf16be_no_bom(self, tmp_path: Path) -> None:
        """Test reading UTF-16 BE file without BOM."""
        from mahlif.sibelius.lint import read_plugin

        plg = tmp_path / "test.plg"
        # UTF-16 BE without BOM - first byte is null
        content = "{ }"
        plg.write_bytes(content.encode("utf-16-be"))

        result = read_plugin(plg)
        assert result == "{ }"


# =============================================================================
# Sibelius CLI
# =============================================================================


class TestSibeliusCLI:
    """Tests for sibelius CLI commands."""

    def test_build_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test sibelius build command via CLI."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        result = sibelius_main(
            ["build", "--source", str(source_dir), "-o", str(output_dir), "-q"]
        )
        assert result == 0

    def test_check_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test sibelius check command via CLI."""
        plg = tmp_path / "test.plg"
        plg.write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        result = sibelius_main(["check", str(plg)])
        assert result == 0
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    def test_check_command_with_fix(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test sibelius check --fix command."""
        plg = tmp_path / "test.plg"
        plg.write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}   """
        )  # Trailing whitespace

        sibelius_main(["check", "--fix", str(plg)])
        # Should succeed after fix
        captured = capsys.readouterr()
        assert "Fixed trailing whitespace" in captured.out

    def test_check_command_with_fix_no_trailing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test sibelius check --fix with no trailing whitespace to fix."""
        plg = tmp_path / "test.plg"
        plg.write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )  # No trailing whitespace

        result = sibelius_main(["check", "--fix", str(plg)])
        assert result == 0
        captured = capsys.readouterr()
        # Should not mention fixing
        assert "Fixed" not in captured.out

    def test_check_command_with_fix_dry_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test sibelius check --fix --dry-run command."""
        plg = tmp_path / "test.plg"
        original = """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}   """
        plg.write_text(original)

        sibelius_main(["check", "--fix", "--dry-run", str(plg)])
        captured = capsys.readouterr()
        assert "Would fix" in captured.out
        # File should be unchanged
        assert plg.read_text() == original

    def test_check_command_file_not_found(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test check with nonexistent file."""
        result = sibelius_main(["check", "/nonexistent/file.plg"])
        assert result >= 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_check_command_with_errors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test check command with lint errors."""
        plg = tmp_path / "test.plg"
        plg.write_text("{ Initialize")  # Missing closing brace

        result = sibelius_main(["check", str(plg)])
        assert result >= 1
        captured = capsys.readouterr()
        assert "error(s)" in captured.out
        assert "E003" in captured.out  # Unclosed brace error

    def test_check_command_default_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test check with no files specified uses default directory."""
        # This will use the package's sibelius directory
        # We mock find_plugin_sources to return an empty list
        with patch("mahlif.sibelius.build.find_plugin_sources", return_value=[]):
            result = sibelius_main(["check"])
        assert result == 0
        captured = capsys.readouterr()
        assert "No .plg files found" in captured.out

    def test_install_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test install command (shortcut for build --install)."""
        sibelius_dir = tmp_path / "sibelius"
        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            result = sibelius_main(["install"])
        assert result == 0
        # Should have installed plugins to sibelius_dir
        assert sibelius_dir.exists()
        assert any(sibelius_dir.glob("*.plg"))

    def test_install_command_dry_run(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test install command with --dry-run."""
        sibelius_dir = tmp_path / "sibelius"
        with patch(
            "mahlif.sibelius.build.get_sibelius_plugin_dir",
            return_value=sibelius_dir,
        ):
            result = sibelius_main(["install", "--dry-run"])
        assert result == 0
        # Should NOT have created directory
        assert not sibelius_dir.exists()
        captured = capsys.readouterr()
        assert "Would build" in captured.out

    def test_list_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test list command shows available plugins."""
        result = sibelius_main(["list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Available plugins:" in captured.out
        assert "MahlifExport" in captured.out

    def test_list_command_empty(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test list command with no plugins."""
        with patch("mahlif.sibelius.build.find_plugin_sources", return_value=[]):
            result = sibelius_main(["list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "No plugins found" in captured.out

    def test_show_plugin_dir_macos(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test show-plugin-dir on macOS."""
        with patch.object(sys, "platform", "darwin"):
            result = sibelius_main(["show-plugin-dir"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Sibelius" in captured.out

    def test_show_plugin_dir_unknown(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test show-plugin-dir on unknown OS."""
        with patch.object(sys, "platform", "linux"):
            result = sibelius_main(["show-plugin-dir"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Could not detect" in captured.out


# =============================================================================
# Integration with Main CLI
# =============================================================================


class TestMainCLIIntegration:
    """Tests for sibelius commands via main CLI."""

    def test_sibelius_build_via_main(self, tmp_path: Path) -> None:
        """Test mahlif sibelius build."""
        from mahlif.cli import main

        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        result = main(
            [
                "sibelius",
                "build",
                "--source",
                str(source_dir),
                "-o",
                str(output_dir),
                "-q",
            ]
        )
        assert result == 0

    def test_sibelius_check_via_main(self, tmp_path: Path) -> None:
        """Test mahlif sibelius check."""
        from mahlif.cli import main

        plg = tmp_path / "test.plg"
        plg.write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        result = main(["sibelius", "check", str(plg)])
        assert result == 0


class TestParseCodes:
    """Tests for _parse_codes helper function."""

    def test_empty_string(self) -> None:
        """Test empty string returns empty set."""
        from mahlif.sibelius.cli import _parse_codes

        assert _parse_codes("") == set()

    def test_single_code(self) -> None:
        """Test single code."""
        from mahlif.sibelius.cli import _parse_codes

        assert _parse_codes("W002") == {"W002"}

    def test_multiple_codes(self) -> None:
        """Test multiple comma-separated codes."""
        from mahlif.sibelius.cli import _parse_codes

        assert _parse_codes("W002,W003,E001") == {"W002", "W003", "E001"}

    def test_whitespace_handling(self) -> None:
        """Test whitespace is stripped."""
        from mahlif.sibelius.cli import _parse_codes

        assert _parse_codes(" W002 , W003 ") == {"W002", "W003"}

    def test_empty_items_ignored(self) -> None:
        """Test empty items are ignored."""
        from mahlif.sibelius.cli import _parse_codes

        assert _parse_codes("W002,,W003") == {"W002", "W003"}


class TestLintFlags:
    """Tests for lint --ignore, --fixable, --unfixable flags."""

    def test_ignore_single_code(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --ignore with single code."""
        plg = tmp_path / "test.plg"
        plg.write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { x = 1;   }"
}"""
        )  # Has trailing whitespace (W002)

        result = sibelius_main(["check", "--ignore", "W002", str(plg)])
        assert result == 0
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    def test_ignore_multiple_codes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --ignore with multiple comma-separated codes."""
        plg = tmp_path / "test.plg"
        # Missing Initialize (W010) and AddToPluginsMenu (W011)
        plg.write_text('{ Run "() { }" }')

        result = sibelius_main(["check", "--ignore", "W010,W011", str(plg)])
        assert result == 0
        captured = capsys.readouterr()
        assert "No issues found" in captured.out

    def test_unfixable_prevents_fix(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --unfixable prevents auto-fix."""
        plg = tmp_path / "test.plg"
        # Write content with actual trailing whitespace at end of line
        plg.write_text(
            "{\n"
            "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
            '    Run "() { }"\n'
            "}"
        )

        sibelius_main(["check", "--fix", "--unfixable", "W002", str(plg)])
        # Should report the warning but not fix it
        captured = capsys.readouterr()
        assert "W002" in captured.out
        assert "Fixed" not in captured.out
        # Verify file still has trailing whitespace
        content = plg.read_text()
        assert '}"   \n' in content

    def test_fixable_limits_fixes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --fixable limits which codes are fixed."""
        plg = tmp_path / "test.plg"
        # Write content with actual trailing whitespace at end of line
        plg.write_text(
            "{\n"
            "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
            '    Run "() { }"\n'
            "}"
        )

        # Only allow E001 to be fixed (not W002)
        sibelius_main(["check", "--fix", "--fixable", "E001", str(plg)])
        captured = capsys.readouterr()
        assert "W002" in captured.out
        assert "Fixed" not in captured.out

    def test_fixable_allows_specified(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test --fixable allows specified codes to be fixed."""
        plg = tmp_path / "test.plg"
        # Write content with actual trailing whitespace at end of line
        plg.write_text(
            "{\n"
            "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
            '    Run "() { }"\n'
            "}"
        )

        result = sibelius_main(["check", "--fix", "--fixable", "W002", str(plg)])
        assert result == 0
        captured = capsys.readouterr()
        assert "Fixed trailing whitespace" in captured.out


class TestManuscriptAlias:
    """Tests for manuscript alias (language-focused alternative to sibelius)."""

    def test_manuscript_check_via_main(self, tmp_path: Path) -> None:
        """Test mahlif manuscript check."""
        from mahlif.cli import main

        plg = tmp_path / "test.plg"
        plg.write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        result = main(["manuscript", "check", str(plg)])
        assert result == 0

    def test_manuscript_build_via_main(self, tmp_path: Path) -> None:
        """Test mahlif manuscript build."""
        from mahlif.cli import main

        source_dir = tmp_path / "src"
        source_dir.mkdir()
        output_dir = tmp_path / "dist"

        (source_dir / "test.plg").write_text(
            """{
    Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
    Run "() { }"
}"""
        )

        result = main(
            [
                "manuscript",
                "build",
                "--source",
                str(source_dir),
                "-o",
                str(output_dir),
                "-q",
            ]
        )
        assert result == 0
        assert (output_dir / "test.plg").exists()

    def test_manuscript_list_via_main(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test mahlif manuscript list."""
        from mahlif.cli import main

        result = main(["manuscript", "list"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Available plugins:" in captured.out
