"""Tests for build_plugins function."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mahlif.sibelius.build import build_plugins
from mahlif.sibelius.build import main as build_main


VALID_PLUGIN = """{
Initialize "() { AddToPluginsMenu('Test', 'Run'); }"
Run "() { }"
}"""


def test_build_plugins_no_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with no plugins found."""
    error_count, built = build_plugins(source_dir=tmp_path)
    assert error_count == 0
    assert built == []
    captured = capsys.readouterr()
    assert "No .plg files found" in captured.out


def test_build_plugins_unresolved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build fails on lint errors."""
    (tmp_path / "bad.plg").write_text("{ Initialize")
    error_count, built = build_plugins(source_dir=tmp_path)
    assert error_count == 1
    assert built == []
    captured = capsys.readouterr()
    assert "Lint errors found" in captured.out


def test_build_plugins_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test successful plugin build."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"

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
    raw = built[0].read_bytes()
    assert raw.startswith(b"\xfe\xff")


def test_build_plugins_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with dry run."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

    error_count, built = build_plugins(
        source_dir=source_dir, output_dir=output_dir, dry_run=True
    )
    assert error_count == 0
    assert len(built) == 1
    assert not (output_dir / "test.plg").exists()
    captured = capsys.readouterr()
    assert "Dry run" in captured.out
    assert "Would build" in captured.out


def test_build_plugins_specific(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test building specific plugins."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"

    (source_dir / "a.plg").write_text(VALID_PLUGIN)
    (source_dir / "b.plg").write_text(VALID_PLUGIN)
    (source_dir / "c.plg").write_text(VALID_PLUGIN)

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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with --install option."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    sibelius_dir = tmp_path / "sibelius"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        error_count, built = build_plugins(source_dir=source_dir, install=True)

    assert error_count == 0
    assert len(built) == 1
    assert built[0].parent == sibelius_dir
    assert (sibelius_dir / "test.plg").exists()


def test_build_plugins_install_no_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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

    link_path = sibelius_dir / "test.plg"
    assert link_path.exists()
    assert link_path.stat().st_ino == built[0].stat().st_ino


def test_build_plugins_hardlink_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with hardlink and dry run."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"
    sibelius_dir = tmp_path / "sibelius"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

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
    assert not (output_dir / "test.plg").exists()
    assert not (sibelius_dir / "test.plg").exists()


def test_build_plugins_hardlink_quiet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with hardlink and quiet mode."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"
    sibelius_dir = tmp_path / "sibelius"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

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
    assert (output_dir / "test.plg").exists()
    assert (sibelius_dir / "test.plg").exists()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_build_plugins_hardlink_no_sibelius_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with hardlink when Sibelius dir not detected."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

    with patch("mahlif.sibelius.build.get_sibelius_plugin_dir", return_value=None):
        error_count, built = build_plugins(
            source_dir=source_dir, output_dir=output_dir, hardlink=True
        )

    assert error_count == 0
    captured = capsys.readouterr()
    assert "Could not detect" in captured.out
    assert "Hardlinks not created" in captured.out


def test_build_plugins_hardlink_overwrites(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with hardlink overwrites existing files."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"
    sibelius_dir = tmp_path / "sibelius"
    sibelius_dir.mkdir()

    (source_dir / "test.plg").write_text(VALID_PLUGIN)
    (sibelius_dir / "test.plg").write_text("old content")

    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        error_count, built = build_plugins(
            source_dir=source_dir, output_dir=output_dir, hardlink=True
        )

    assert error_count == 0
    assert (sibelius_dir / "test.plg").read_bytes().startswith(b"\xfe\xff")


def test_build_main(tmp_path: Path) -> None:
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


def test_build_main_with_plugins(tmp_path: Path) -> None:
    """Test build main with specific plugins."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"

    (source_dir / "a.plg").write_text(VALID_PLUGIN)
    (source_dir / "b.plg").write_text(VALID_PLUGIN)

    result = build_main(["a", "--source", str(source_dir), "-o", str(output_dir), "-q"])
    assert result == 0
    assert (output_dir / "a.plg").exists()
    assert not (output_dir / "b.plg").exists()


def test_build_plugins_quiet_no_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with quiet mode and no source."""
    error_count, built = build_plugins(source_dir=tmp_path, verbose=False)
    assert error_count == 0
    assert built == []
    captured = capsys.readouterr()
    assert captured.out == ""


def test_build_plugins_quiet_unresolved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with quiet mode and lint errors."""
    (tmp_path / "bad.plg").write_text("{ Initialize")
    error_count, built = build_plugins(source_dir=tmp_path, verbose=False)
    assert error_count == 1
    captured = capsys.readouterr()
    assert captured.out == ""


def test_build_plugins_quiet_install_no_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with quiet mode, hardlink, but no Sibelius dir."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "dist"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

    with patch("mahlif.sibelius.build.get_sibelius_plugin_dir", return_value=None):
        error_count, built = build_plugins(
            source_dir=source_dir,
            output_dir=output_dir,
            hardlink=True,
            verbose=False,
        )

    assert error_count == 0
    captured = capsys.readouterr()
    assert "Linting" not in captured.out


def test_build_plugins_default_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with default source_dir (package directory)."""
    output_dir = tmp_path / "dist"
    error_count, built = build_plugins(output_dir=output_dir)
    assert error_count == 0
    assert len(built) > 0
    assert any("MahlifExport" in str(p) for p in built)


def test_build_plugins_install_with_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with --install and explicit output_dir."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    output_dir = tmp_path / "custom_output"
    sibelius_dir = tmp_path / "sibelius"

    (source_dir / "test.plg").write_text(VALID_PLUGIN)

    with patch(
        "mahlif.sibelius.build.get_sibelius_plugin_dir",
        return_value=sibelius_dir,
    ):
        error_count, built = build_plugins(
            source_dir=source_dir,
            output_dir=output_dir,
            install=True,
        )

    assert error_count == 0
    assert built[0].parent == output_dir


def test_build_plugins_unresolved_no_available(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test build with unresolved plugins and no available plugins."""
    error_count, built = build_plugins(
        source_dir=tmp_path, plugin_names=["nonexistent"]
    )
    assert error_count == 1
    captured = capsys.readouterr()
    assert "Could not find plugins" in captured.out
    assert "Available:" not in captured.out


def test_build_plugins_hardlink_already_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test build with hardlink when hardlink already exists (same inode)."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    plugin = source_dir / "Test.plg"
    plugin.write_text('{\n    Run "() {\n        x = 1;\n    }"\n}\n', encoding="utf-8")

    output_dir = tmp_path / "dist"
    sibelius_dir = tmp_path / "sibelius_plugins"
    sibelius_dir.mkdir()

    monkeypatch.setattr(
        "mahlif.sibelius.build.get_sibelius_plugin_dir", lambda: sibelius_dir
    )

    error_count, built = build_plugins(
        source_dir=source_dir, output_dir=output_dir, hardlink=True
    )
    assert error_count == 0

    link_path = sibelius_dir / "Test.plg"
    assert link_path.exists()
    original_inode = link_path.stat().st_ino

    error_count, built = build_plugins(
        source_dir=source_dir, output_dir=output_dir, hardlink=True
    )
    assert error_count == 0
    assert link_path.stat().st_ino == original_inode
