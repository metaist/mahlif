"""Tests for plugin resolution functions."""

from __future__ import annotations

from pathlib import Path

from mahlif.sibelius.build import find_plugin_sources
from mahlif.sibelius.build import resolve_plugins


def test_find_plugin_sources(tmp_path: Path) -> None:
    """Test finding plugin source files."""
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
    assert "hidden.plg" not in names


def test_find_plugin_sources_empty(tmp_path: Path) -> None:
    """Test finding plugins in empty directory."""
    plugins = find_plugin_sources(tmp_path)
    assert plugins == []


def test_resolve_plugins_empty(tmp_path: Path) -> None:
    """Test resolve_plugins with empty list returns all."""
    (tmp_path / "a.plg").write_text("{}")
    (tmp_path / "b.plg").write_text("{}")
    resolved, unresolved = resolve_plugins(tmp_path, [])
    assert len(resolved) == 2
    assert unresolved == []


def test_resolve_plugins_by_name(tmp_path: Path) -> None:
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


def test_resolve_plugins_by_path(tmp_path: Path) -> None:
    """Test resolve_plugins by path."""
    plg = tmp_path / "test.plg"
    plg.write_text("{}")
    resolved, unresolved = resolve_plugins(tmp_path, [str(plg)])
    assert len(resolved) == 1
    assert resolved[0] == plg
    assert unresolved == []


def test_resolve_plugins_mixed(tmp_path: Path) -> None:
    """Test resolve_plugins with names and paths."""
    (tmp_path / "a.plg").write_text("{}")
    external = tmp_path / "external" / "b.plg"
    external.parent.mkdir()
    external.write_text("{}")

    resolved, unresolved = resolve_plugins(tmp_path, ["a", str(external)])
    assert len(resolved) == 2
    assert unresolved == []


def test_resolve_plugins_unresolved(tmp_path: Path) -> None:
    """Test resolve_plugins with unresolved names."""
    (tmp_path / "a.plg").write_text("{}")
    resolved, unresolved = resolve_plugins(tmp_path, ["a", "nonexistent"])
    assert len(resolved) == 1
    assert unresolved == ["nonexistent"]


def test_resolve_plugins_path_not_found(tmp_path: Path) -> None:
    """Test resolve_plugins with non-existent path."""
    resolved, unresolved = resolve_plugins(tmp_path, ["./nonexistent.plg"])
    assert resolved == []
    assert unresolved == ["./nonexistent.plg"]
