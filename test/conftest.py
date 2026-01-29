"""Pytest configuration - catch unmocked AppleScript calls."""

import subprocess
import traceback

import pytest

_original_run = subprocess.run


def _guarded_run(*args, **kwargs):
    """Raise if osascript is called without mocking."""
    if args and "osascript" in str(args[0]):
        tb = "".join(traceback.format_stack())
        raise RuntimeError(
            f"UNMOCKED osascript call detected!\nArgs: {args}\nTraceback:\n{tb}"
        )
    return _original_run(*args, **kwargs)


@pytest.fixture(autouse=True)
def guard_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically guard against unmocked subprocess calls in all tests."""
    monkeypatch.setattr(subprocess, "run", _guarded_run)
