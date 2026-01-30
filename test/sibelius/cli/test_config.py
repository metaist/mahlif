"""Tests for config file integration and lint flags."""

from __future__ import annotations

from pathlib import Path

import pytest

from mahlif.sibelius.cli import _parse_codes
from mahlif.sibelius.cli import main as sibelius_main


# =============================================================================
# _parse_codes helper tests
# =============================================================================


def test_empty_string() -> None:
    """Test empty string returns empty set."""
    assert _parse_codes("") == set()


def test_single_code() -> None:
    """Test single code."""
    assert _parse_codes("MS-W002") == {"MS-W002"}


def test_multiple_codes() -> None:
    """Test multiple comma-separated codes."""
    assert _parse_codes("MS-W002,MS-W003,MS-E001") == {
        "MS-W002",
        "MS-W003",
        "MS-E001",
    }


def test_whitespace_handling() -> None:
    """Test whitespace is stripped."""
    assert _parse_codes(" MS-W002 , MS-W003 ") == {"MS-W002", "MS-W003"}


def test_empty_items_ignored() -> None:
    """Test empty items are ignored."""
    assert _parse_codes("MS-W002,,MS-W003") == {"MS-W002", "MS-W003"}


# =============================================================================
# --ignore, --fixable, --unfixable flags
# =============================================================================


def test_ignore_single_code(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test --ignore with single code."""
    plg = tmp_path / "test.plg"
    plg.write_text(
        """{
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
Run "() { return 1;   }"
}"""
    )

    result = sibelius_main(["check", "--ignore", "MS-W002", str(plg)])
    assert result == 0
    captured = capsys.readouterr()
    assert "No issues found" in captured.out


def test_ignore_multiple_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --ignore with multiple comma-separated codes."""
    plg = tmp_path / "test.plg"
    plg.write_text('{ Run "() { }" }')

    result = sibelius_main(["check", "--ignore", "MS-W010,MS-W011", str(plg)])
    assert result == 0
    captured = capsys.readouterr()
    assert "No issues found" in captured.out


def test_unfixable_prevents_fix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --unfixable prevents auto-fix."""
    plg = tmp_path / "test.plg"
    plg.write_text(
        "{\n"
        "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
        '    Run "() { }"\n'
        "}"
    )

    sibelius_main(["check", "--fix", "--unfixable", "MS-W002", str(plg)])
    captured = capsys.readouterr()
    assert "MS-W002" in captured.out
    assert "Fixed" not in captured.out
    content = plg.read_text()
    assert '}"   \n' in content


def test_fixable_limits_fixes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --fixable limits which codes are fixed."""
    plg = tmp_path / "test.plg"
    plg.write_text(
        "{\n"
        "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
        '    Run "() { }"\n'
        "}"
    )

    sibelius_main(["check", "--fix", "--fixable", "MS-E001", str(plg)])
    captured = capsys.readouterr()
    assert "MS-W002" in captured.out
    assert "Fixed" not in captured.out


def test_fixable_allows_specified(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --fixable allows specified codes to be fixed."""
    plg = tmp_path / "test.plg"
    plg.write_text(
        "{\n"
        "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
        '    Run "() { }"\n'
        "}"
    )

    result = sibelius_main(["check", "--fix", "--fixable", "MS-W002", str(plg)])
    assert result == 0
    captured = capsys.readouterr()
    assert "Fixed trailing whitespace" in captured.out


# =============================================================================
# Config file integration
# =============================================================================


def test_config_ignore_from_mahlif_toml(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test --ignore from mahlif.toml."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text('[sibelius.lint]\nignore = ["MS-W010", "MS-W011"]')

    plg = tmp_path / "test.plg"
    plg.write_text('{ Run "() { }" }')

    monkeypatch.chdir(tmp_path)
    result = sibelius_main(["check", str(plg)])
    assert result == 0
    captured = capsys.readouterr()
    assert "No issues found" in captured.out


def test_cli_overrides_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test CLI flags merge with config (both are applied)."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text('[sibelius.lint]\nignore = ["MS-W010"]')

    plg = tmp_path / "test.plg"
    plg.write_text('{ Run "() { }" }')

    monkeypatch.chdir(tmp_path)

    result = sibelius_main(["check", "--ignore", "MS-W011", str(plg)])
    assert result == 0
    captured = capsys.readouterr()
    assert "No issues found" in captured.out


def test_config_unfixable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test unfixable from config file."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text('[sibelius.lint]\nunfixable = ["MS-W002"]')

    plg = tmp_path / "test.plg"
    plg.write_text(
        "{\n"
        "    Initialize \"() { AddToPluginsMenu('Test', 'Run'); }\"   \n"
        '    Run "() { }"\n'
        "}"
    )

    monkeypatch.chdir(tmp_path)
    sibelius_main(["check", "--fix", str(plg)])
    captured = capsys.readouterr()
    assert "MS-W002" in captured.out
    assert "Fixed" not in captured.out
