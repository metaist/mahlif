"""Tests for encoding/conversion functions."""

from __future__ import annotations

from pathlib import Path

from mahlif.sibelius.build import convert_to_utf16be
from mahlif.sibelius.manuscript.lint import fix_trailing_whitespace
from mahlif.sibelius.manuscript.lint import read_plugin


def test_convert_to_utf16be() -> None:
    """Test UTF-16 BE conversion."""
    content = "Hello\nWorld"
    result = convert_to_utf16be(content)
    assert result[:2] == b"\xfe\xff"
    decoded = result[2:].decode("utf-16-be")
    assert decoded == "Hello\nWorld"


def test_convert_to_utf16be_strips_trailing_whitespace() -> None:
    """Test that trailing whitespace is stripped."""
    content = "Line 1   \nLine 2\t\nLine 3"
    result = convert_to_utf16be(content)
    decoded = result[2:].decode("utf-16-be")
    assert decoded == "Line 1\nLine 2\nLine 3"


def test_fix_trailing_whitespace_utf8(tmp_path: Path) -> None:
    """Test fixing trailing whitespace in UTF-8 file."""
    plg = tmp_path / "test.plg"
    plg.write_text("Line 1   \nLine 2\t\nLine 3", encoding="utf-8")

    changed = fix_trailing_whitespace(plg)
    assert changed

    content = plg.read_text(encoding="utf-8")
    assert content == "Line 1\nLine 2\nLine 3"


def test_fix_trailing_whitespace_utf16be(tmp_path: Path) -> None:
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


def test_fix_trailing_whitespace_utf16le(tmp_path: Path) -> None:
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


def test_fix_trailing_whitespace_no_change(tmp_path: Path) -> None:
    """Test no change when no trailing whitespace."""
    plg = tmp_path / "test.plg"
    plg.write_text("Line 1\nLine 2", encoding="utf-8")

    changed = fix_trailing_whitespace(plg)
    assert not changed


def test_read_plugin_utf16be_no_bom(tmp_path: Path) -> None:
    """Test reading UTF-16 BE file without BOM."""
    plg = tmp_path / "test.plg"
    content = "{ }"
    plg.write_bytes(content.encode("utf-16-be"))

    result = read_plugin(plg)
    assert result == "{ }"
