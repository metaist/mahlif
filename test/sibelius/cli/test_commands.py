"""Tests for CLI commands (check, install, list, format, etc.)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mahlif.sibelius.build import get_sibelius_plugin_dir
from mahlif.sibelius.cli import main as sibelius_main


def test_macos() -> None:
    """Test macOS plugin directory."""
    with patch.object(sys, "platform", "darwin"):
        result = get_sibelius_plugin_dir()
        assert result is not None
        assert "Library/Application Support/Avid/Sibelius" in str(result)


def test_windows() -> None:
    """Test Windows plugin directory."""
    with patch.object(sys, "platform", "win32"):
        result = get_sibelius_plugin_dir()
        assert result is not None
        assert "Avid/Sibelius" in str(result) or "Avid\\Sibelius" in str(result)


def test_linux() -> None:
    """Test Linux returns None."""
    with patch.object(sys, "platform", "linux"):
        result = get_sibelius_plugin_dir()
        assert result is None


def test_build_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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


def test_check_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test sibelius check --fix command."""
    plg = tmp_path / "test.plg"
    plg.write_text(
        """{
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
Run "() { }"
}   """
    )

    sibelius_main(["check", "--fix", str(plg)])
    captured = capsys.readouterr()
    assert "Fixed trailing whitespace" in captured.out


def test_check_command_with_fix_no_trailing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test sibelius check --fix with no trailing whitespace to fix."""
    plg = tmp_path / "test.plg"
    plg.write_text(
        """{
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
Run "() { }"
}"""
    )

    result = sibelius_main(["check", "--fix", str(plg)])
    assert result == 0
    captured = capsys.readouterr()
    assert "Fixed" not in captured.out


def test_check_command_with_fix_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    assert plg.read_text() == original


def test_check_command_file_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    """Test check with nonexistent file."""
    result = sibelius_main(["check", "/nonexistent/file.plg"])
    assert result >= 1
    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_check_command_with_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test check command with lint errors."""
    plg = tmp_path / "test.plg"
    plg.write_text("{ Initialize")

    result = sibelius_main(["check", str(plg)])
    assert result >= 1
    captured = capsys.readouterr()
    assert "error(s)" in captured.out
    assert "MS-E003" in captured.out


def test_check_command_default_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test check with no files specified uses default directory."""
    with patch("mahlif.sibelius.build.find_plugin_sources", return_value=[]):
        result = sibelius_main(["check"])
    assert result == 0
    captured = capsys.readouterr()
    assert "No .plg files found" in captured.out


def test_install_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test install command installs MahlifExport by default."""
    sibelius_dir = tmp_path / "sibelius"
    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        result = sibelius_main(["install"])
    assert result == 0
    assert sibelius_dir.exists()
    # Should only install MahlifExport by default
    plugins = list(sibelius_dir.glob("*.plg"))
    assert len(plugins) == 1
    assert plugins[0].stem == "MahlifExport"


def test_install_command_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test install command with --dry-run."""
    sibelius_dir = tmp_path / "sibelius"
    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        result = sibelius_main(["install", "--dry-run"])
    assert result == 0
    assert not sibelius_dir.exists()
    captured = capsys.readouterr()
    assert "Would build" in captured.out
    assert "MahlifExport" in captured.out


def test_install_command_specific_plugin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test install command with specific plugin name."""
    sibelius_dir = tmp_path / "sibelius"
    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        result = sibelius_main(["install", "Cyrus"])
    assert result == 0
    plugins = list(sibelius_dir.glob("*.plg"))
    assert len(plugins) == 1
    assert plugins[0].stem == "Cyrus"


def test_install_command_multiple_plugins(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test install command with multiple plugin names."""
    sibelius_dir = tmp_path / "sibelius"
    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        result = sibelius_main(["install", "MahlifExport", "Cyrus"])
    assert result == 0
    plugins = list(sibelius_dir.glob("*.plg"))
    assert len(plugins) == 2
    names = {p.stem for p in plugins}
    assert names == {"MahlifExport", "Cyrus"}


def test_list_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Test list command shows available plugins."""
    result = sibelius_main(["list"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Available plugins:" in captured.out
    assert "MahlifExport" in captured.out


def test_list_command_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test list command with no plugins."""
    with patch("mahlif.sibelius.build.find_plugin_sources", return_value=[]):
        result = sibelius_main(["list"])
    assert result == 0
    captured = capsys.readouterr()
    assert "No plugins found" in captured.out


def test_show_plugin_dir_macos(capsys: pytest.CaptureFixture[str]) -> None:
    """Test show-plugin-dir on macOS."""
    with patch.object(sys, "platform", "darwin"):
        result = sibelius_main(["show-plugin-dir"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Sibelius" in captured.out


def test_show_plugin_dir_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    """Test show-plugin-dir on unknown OS."""
    with patch.object(sys, "platform", "linux"):
        result = sibelius_main(["show-plugin-dir"])
    assert result == 1
    captured = capsys.readouterr()
    assert "Could not detect" in captured.out


def test_sibelius_build_via_main(tmp_path: Path) -> None:
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


def test_sibelius_check_via_main(tmp_path: Path) -> None:
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


def test_manuscript_check_via_main(tmp_path: Path) -> None:
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


def test_manuscript_build_via_main(tmp_path: Path) -> None:
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


def test_manuscript_list_via_main(capsys: pytest.CaptureFixture[str]) -> None:
    """Test mahlif manuscript list."""
    from mahlif.cli import main

    result = main(["manuscript", "list"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Available plugins:" in captured.out


def test_format_already_formatted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test format command with already formatted file."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{\n    Run "() {\n        x = 1;\n    }"\n}\n', encoding="utf-8")

    result = sibelius_main(["format", str(plugin)])
    assert result == 0
    captured = capsys.readouterr()
    assert "Already formatted" in captured.out


def test_format_reformats_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test format command reformats unformatted file."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{Run "() { x=1; }"}', encoding="utf-8")

    result = sibelius_main(["format", str(plugin)])
    assert result == 0
    captured = capsys.readouterr()
    assert "Reformatted" in captured.out


def test_format_check_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test format --check reports unformatted files."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{Run "() { x=1; }"}', encoding="utf-8")

    result = sibelius_main(["format", "--check", str(plugin)])
    assert result == 1
    captured = capsys.readouterr()
    assert "Would reformat" in captured.out


def test_format_check_mode_already_formatted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test format --check passes for formatted file."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{\n    Run "() {\n        x = 1;\n    }"\n}\n', encoding="utf-8")

    result = sibelius_main(["format", "--check", str(plugin)])
    assert result == 0


def test_format_diff_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test format --diff shows diff."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{Run "() { x=1; }"}', encoding="utf-8")

    result = sibelius_main(["format", "--diff", str(plugin)])
    assert result == 0
    captured = capsys.readouterr()
    assert "---" in captured.out or "+++" in captured.out


def test_format_file_not_found(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test format with nonexistent file."""
    sibelius_main(["format", str(tmp_path / "nonexistent.plg")])
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_format_default_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test format with no files uses default directory."""
    sibelius_dir = tmp_path / "sibelius"
    sibelius_dir.mkdir()
    plugin = sibelius_dir / "Test.plg"
    plugin.write_text('{\n    Run "() {\n        x = 1;\n    }"\n}\n', encoding="utf-8")

    import mahlif.sibelius.cli as cli_module

    monkeypatch.setattr(cli_module, "__file__", str(sibelius_dir / "cli.py"))

    result = sibelius_main(["format"])
    assert result == 0


def test_check_strict_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test check --strict treats warnings as errors."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{\n    Run "() {\n        x = 1;\n    }"\n}\n', encoding="utf-8")

    result = sibelius_main(["check", "--strict", str(plugin)])
    assert result >= 1
    captured = capsys.readouterr()
    assert "error(s)" in captured.out


def test_check_error_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test check --error promotes specific warnings to errors."""
    plugin = tmp_path / "Test.plg"
    plugin.write_text('{\n    Run "() {\n        x = 1;\n    }"\n}\n', encoding="utf-8")

    result = sibelius_main(["check", "--error=MS-W025", str(plugin)])
    assert result >= 1
    captured = capsys.readouterr()
    assert "error(s)" in captured.out
