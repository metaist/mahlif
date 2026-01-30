"""Tests for helper functions in convert module."""

from __future__ import annotations

import tempfile
from pathlib import Path

from mahlif.sibelius.convert import ARTICULATION_MAP
from mahlif.sibelius.convert import _calc_spanner_duration
from mahlif.sibelius.convert import convert_to_utf16
from mahlif.sibelius.convert import escape_str
from mahlif.sibelius.convert import write_plugin


def test_escape_str_basic() -> None:
    """Test basic string escaping."""
    assert escape_str("hello") == "hello"
    assert escape_str("it's") == "it\\'s"
    assert escape_str("back\\slash") == "back\\\\slash"
    assert escape_str("it's a\\b") == "it\\'s a\\\\b"


def test_calc_spanner_duration_same_bar() -> None:
    """Test duration calculation within same bar."""
    result = _calc_spanner_duration(1, 0, 1, 256, 1024)
    assert result == 256


def test_calc_spanner_duration_cross_bar() -> None:
    """Test duration calculation across bars."""
    result = _calc_spanner_duration(1, 512, 3, 256, 1024)
    assert result == 1792


def test_articulation_map_coverage() -> None:
    """Test that articulation map has expected entries."""
    assert "staccato" in ARTICULATION_MAP
    assert "fermata" in ARTICULATION_MAP
    assert ARTICULATION_MAP["fermata"] == "PauseArtic"
    assert "up-bow" in ARTICULATION_MAP
    assert "down-bow" in ARTICULATION_MAP


def test_convert_to_utf16() -> None:
    """Test converting to UTF-16 BE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "test.txt"
        dst = Path(tmpdir) / "test.plg"
        src.write_text("Hello", encoding="utf-8")
        convert_to_utf16(src, dst)

        data = dst.read_bytes()
        assert data[:2] == b"\xfe\xff"
        content = data[2:].decode("utf-16-be")
        assert content == "Hello"


def test_write_plugin() -> None:
    """Test write_plugin writes UTF-16 BE with BOM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / "test.plg"
        write_plugin(dst, "Test content")

        data = dst.read_bytes()
        assert data[:2] == b"\xfe\xff"
        content = data[2:].decode("utf-16-be")
        assert content == "Test content"
