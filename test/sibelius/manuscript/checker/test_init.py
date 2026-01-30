"""Tests for checker module initialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from mahlif.sibelius.manuscript.checker import BUILTIN_GLOBALS


def test_builtin_globals_loaded() -> None:
    """Test that built-in globals are loaded from lang.json."""
    assert len(BUILTIN_GLOBALS) > 50
    assert "Sibelius" in BUILTIN_GLOBALS
    assert "True" in BUILTIN_GLOBALS
    assert "CreateSparseArray" in BUILTIN_GLOBALS


def test_missing_lang_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test error when lang.json is missing."""
    from mahlif.sibelius.manuscript import checker

    fake_path = tmp_path / "nonexistent.json"
    monkeypatch.setattr(checker, "LANG_JSON_PATH", fake_path)

    with pytest.raises(FileNotFoundError, match="Required language data file"):
        checker._load_lang_data()
