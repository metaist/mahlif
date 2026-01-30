"""Configuration file loading for mahlif.

Searches for configuration in:
1. mahlif.toml (primary)
2. pyproject.toml [tool.mahlif] (fallback)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import cast

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found]


@dataclass
class LintConfig:
    """Configuration for linting."""

    ignore: set[str] = field(default_factory=set)
    fixable: set[str] = field(default_factory=set)
    unfixable: set[str] = field(default_factory=set)
    error: set[str] = field(default_factory=set)  # warnings to treat as errors
    strict: bool = False  # treat all warnings as errors


@dataclass
class SibeliusConfig:
    """Configuration for Sibelius/ManuScript tools."""

    lint: LintConfig = field(default_factory=LintConfig)


@dataclass
class MahlifConfig:
    """Root configuration for mahlif."""

    sibelius: SibeliusConfig = field(default_factory=SibeliusConfig)


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Find configuration file, searching upward from start_dir.

    Args:
        start_dir: Directory to start searching from (default: cwd)

    Returns:
        Path to config file, or None if not found
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while True:
        # Check for mahlif.toml first
        mahlif_toml = current / "mahlif.toml"
        if mahlif_toml.exists():
            return mahlif_toml

        # Check for pyproject.toml
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            # Verify it has [tool.mahlif] section
            try:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                if "tool" in data and "mahlif" in data["tool"]:
                    return pyproject
            except Exception:
                pass

        # Move up to parent
        parent = current.parent
        if parent == current:
            # Reached root
            return None
        current = parent


def load_config(path: Path | None = None) -> MahlifConfig:
    """Load configuration from file.

    Args:
        path: Path to config file. If None, searches for one.

    Returns:
        MahlifConfig with loaded values (or defaults if no config found)
    """
    if path is None:
        path = find_config_file()

    if path is None:
        return MahlifConfig()

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return MahlifConfig()

    # Handle pyproject.toml (nested under [tool.mahlif])
    if path.name == "pyproject.toml":
        data = data.get("tool", {}).get("mahlif", {})

    return _parse_config(data)


def _parse_config(data: dict[str, Any]) -> MahlifConfig:
    """Parse config dictionary into MahlifConfig.

    Args:
        data: Raw config dictionary

    Returns:
        Parsed MahlifConfig
    """
    config = MahlifConfig()

    sibelius_data = data.get("sibelius")
    if not isinstance(sibelius_data, dict):
        return config

    lint_data = sibelius_data.get("lint")
    if isinstance(lint_data, dict):
        config.sibelius.lint = _parse_lint_config(cast(dict[str, Any], lint_data))

    return config


def _parse_lint_config(data: dict[str, Any]) -> LintConfig:
    """Parse lint config section.

    Args:
        data: Raw lint config dictionary

    Returns:
        Parsed LintConfig
    """
    config = LintConfig()

    ignore = data.get("ignore", [])
    if isinstance(ignore, list):
        config.ignore = {str(code) for code in ignore if code}

    fixable = data.get("fixable", [])
    if isinstance(fixable, list):
        config.fixable = {str(code) for code in fixable if code}

    unfixable = data.get("unfixable", [])
    if isinstance(unfixable, list):
        config.unfixable = {str(code) for code in unfixable if code}

    error = data.get("error", [])
    if isinstance(error, list):
        config.error = {str(code) for code in error if code}

    strict = data.get("strict", False)
    if isinstance(strict, bool):
        config.strict = strict

    return config
