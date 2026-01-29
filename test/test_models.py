"""Tests for mahlif data models."""

from __future__ import annotations

from mahlif.models import Movement
from mahlif.models import Note
from mahlif.models import NoteRest
from mahlif.models import Position
from mahlif.models import Score


# ----------------------------------------------------------------------
# TestNoteRest: Test NoteRest model.
# ----------------------------------------------------------------------


def test_is_rest() -> None:
    """A NoteRest with no notes is a rest."""
    nr = NoteRest(pos=0, dur=256)
    assert nr.is_rest is True
    assert nr.is_chord is False


def test_single_note() -> None:
    """A NoteRest with one note is not a chord."""
    nr = NoteRest(pos=0, dur=256, notes=[Note(pitch=60)])
    assert nr.is_rest is False
    assert nr.is_chord is False


def test_chord() -> None:
    """A NoteRest with multiple notes is a chord."""
    nr = NoteRest(
        pos=0,
        dur=256,
        notes=[Note(pitch=60), Note(pitch=64), Note(pitch=67)],
    )
    assert nr.is_rest is False
    assert nr.is_chord is True


# ----------------------------------------------------------------------
# TestScore: Test Score model.
# ----------------------------------------------------------------------


def test_single_movement() -> None:
    """A score with no movements is single-movement."""
    score = Score()
    assert score.is_multi_movement is False


def test_multi_movement() -> None:
    """A score with movements is multi-movement."""
    score = Score(movements=[Movement(n=1), Movement(n=2)])
    assert score.is_multi_movement is True


# ----------------------------------------------------------------------
# TestPosition: Test Position model.
# ----------------------------------------------------------------------


def test_defaults() -> None:
    """Position defaults to zero offsets."""
    pos = Position()
    assert pos.dx == 0.0
    assert pos.dy == 0.0
