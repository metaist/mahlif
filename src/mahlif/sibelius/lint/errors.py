"""Lint error type for ManuScript linting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LintError:
    """A linting error."""

    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.line}:{self.col} [{self.code}] {self.message}"
