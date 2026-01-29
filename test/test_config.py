"""Tests for mahlif configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from mahlif.config import LintConfig
from mahlif.config import MahlifConfig
from mahlif.config import SibeliusConfig
from mahlif.config import _parse_config
from mahlif.config import _parse_lint_config
from mahlif.config import find_config_file
from mahlif.config import load_config


# ----------------------------------------------------------------------
# TestFindConfigFile: Tests for find_config_file function.
# ----------------------------------------------------------------------


def test_finds_mahlif_toml(tmp_path: Path) -> None:
    """Test finding mahlif.toml in current directory."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text("[sibelius.lint]\nignore = []")

    result = find_config_file(tmp_path)
    assert result == config_file


def test_finds_pyproject_with_mahlif_section(tmp_path: Path) -> None:
    """Test finding pyproject.toml with [tool.mahlif] section."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mahlif.sibelius.lint]\nignore = []")

    result = find_config_file(tmp_path)
    assert result == pyproject


def test_ignores_pyproject_without_mahlif(tmp_path: Path) -> None:
    """Test ignoring pyproject.toml without [tool.mahlif] section."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.other]\nfoo = 1")

    result = find_config_file(tmp_path)
    assert result is None


def test_prefers_mahlif_toml_over_pyproject(tmp_path: Path) -> None:
    """Test mahlif.toml is preferred over pyproject.toml."""
    mahlif_toml = tmp_path / "mahlif.toml"
    mahlif_toml.write_text("[sibelius.lint]\nignore = ['MS-W002']")

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mahlif.sibelius.lint]\nignore = ['MS-W003']")

    result = find_config_file(tmp_path)
    assert result == mahlif_toml


def test_searches_parent_directories(tmp_path: Path) -> None:
    """Test searching parent directories for config."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text("[sibelius.lint]\nignore = []")

    subdir = tmp_path / "src" / "deep" / "nested"
    subdir.mkdir(parents=True)

    result = find_config_file(subdir)
    assert result == config_file


def test_returns_none_when_not_found(tmp_path: Path) -> None:
    """Test returning None when no config found."""
    result = find_config_file(tmp_path)
    assert result is None


def test_handles_invalid_toml(tmp_path: Path) -> None:
    """Test handling invalid TOML in pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("invalid [ toml")

    result = find_config_file(tmp_path)
    assert result is None


def test_default_start_dir_is_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test default start_dir is current working directory."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text("[sibelius.lint]")
    monkeypatch.chdir(tmp_path)

    result = find_config_file()
    assert result == config_file


# ----------------------------------------------------------------------
# TestLoadConfig: Tests for load_config function.
# ----------------------------------------------------------------------


def test_loads_mahlif_toml(tmp_path: Path) -> None:
    """Test loading from mahlif.toml."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text(
        """
[sibelius.lint]
ignore = ["MS-W002", "MS-W003"]
fixable = ["MS-W002"]
unfixable = ["MS-E001"]
"""
    )

    config = load_config(config_file)
    assert config.sibelius.lint.ignore == {"MS-W002", "MS-W003"}
    assert config.sibelius.lint.fixable == {"MS-W002"}
    assert config.sibelius.lint.unfixable == {"MS-E001"}


def test_loads_pyproject_toml(tmp_path: Path) -> None:
    """Test loading from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.mahlif.sibelius.lint]
ignore = ["MS-W002"]
"""
    )

    config = load_config(pyproject)
    assert config.sibelius.lint.ignore == {"MS-W002"}


def test_returns_defaults_when_no_config(tmp_path: Path) -> None:
    """Test returning default config when no file found."""
    config = load_config(tmp_path / "nonexistent.toml")
    assert config.sibelius.lint.ignore == set()
    assert config.sibelius.lint.fixable == set()
    assert config.sibelius.lint.unfixable == set()


def test_returns_defaults_for_invalid_toml(tmp_path: Path) -> None:
    """Test returning default config for invalid TOML."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text("invalid [ toml")

    config = load_config(config_file)
    assert config.sibelius.lint.ignore == set()


def test_searches_for_config_when_path_is_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test searching for config when path is None."""
    config_file = tmp_path / "mahlif.toml"
    config_file.write_text('[sibelius.lint]\nignore = ["MS-W002"]')
    monkeypatch.chdir(tmp_path)

    config = load_config()
    assert config.sibelius.lint.ignore == {"MS-W002"}


# ----------------------------------------------------------------------
# TestParseConfig: Tests for _parse_config function.
# ----------------------------------------------------------------------


def test_parses_complete_config() -> None:
    """Test parsing complete config structure."""
    data = {
        "sibelius": {
            "lint": {
                "ignore": ["MS-W002"],
                "fixable": ["MS-W002"],
                "unfixable": ["MS-E001"],
            }
        }
    }
    config = _parse_config(data)
    assert config.sibelius.lint.ignore == {"MS-W002"}
    assert config.sibelius.lint.fixable == {"MS-W002"}
    assert config.sibelius.lint.unfixable == {"MS-E001"}


def test_handles_empty_config() -> None:
    """Test parsing empty config."""
    config = _parse_config({})
    assert config.sibelius.lint.ignore == set()


def test_handles_non_dict_sibelius() -> None:
    """Test handling non-dict sibelius value."""
    config = _parse_config({"sibelius": "not a dict"})
    assert config.sibelius.lint.ignore == set()


def test_handles_non_dict_lint() -> None:
    """Test handling non-dict lint value."""
    config = _parse_config({"sibelius": {"lint": "not a dict"}})
    assert config.sibelius.lint.ignore == set()


# ----------------------------------------------------------------------
# TestParseLintConfig: Tests for _parse_lint_config function.
# ----------------------------------------------------------------------


def test_parses_all_fields() -> None:
    """Test parsing all lint config fields."""
    data = {
        "ignore": ["MS-W002", "MS-W003"],
        "fixable": ["MS-W002"],
        "unfixable": ["MS-E001"],
    }
    config = _parse_lint_config(data)
    assert config.ignore == {"MS-W002", "MS-W003"}
    assert config.fixable == {"MS-W002"}
    assert config.unfixable == {"MS-E001"}


def test_handles_empty_lists() -> None:
    """Test handling empty lists."""
    data: dict[str, list[str]] = {"ignore": [], "fixable": [], "unfixable": []}
    config = _parse_lint_config(data)
    assert config.ignore == set()
    assert config.fixable == set()
    assert config.unfixable == set()


def test_handles_missing_fields() -> None:
    """Test handling missing fields."""
    config = _parse_lint_config({})
    assert config.ignore == set()
    assert config.fixable == set()
    assert config.unfixable == set()


def test_handles_non_list_values() -> None:
    """Test handling non-list values."""
    data = {"ignore": "not a list", "fixable": 123, "unfixable": None}
    config = _parse_lint_config(data)
    assert config.ignore == set()
    assert config.fixable == set()
    assert config.unfixable == set()


def test_filters_empty_values() -> None:
    """Test filtering empty/falsy values in lists."""
    data = {"ignore": ["MS-W002", "", None, "MS-W003"]}
    config = _parse_lint_config(data)
    assert config.ignore == {"MS-W002", "MS-W003"}


# ----------------------------------------------------------------------
# TestDataclasses: Tests for config dataclasses.
# ----------------------------------------------------------------------


def test_lint_config_defaults() -> None:
    """Test LintConfig default values."""
    config = LintConfig()
    assert config.ignore == set()
    assert config.fixable == set()
    assert config.unfixable == set()


def test_sibelius_config_defaults() -> None:
    """Test SibeliusConfig default values."""
    config = SibeliusConfig()
    assert isinstance(config.lint, LintConfig)


def test_mahlif_config_defaults() -> None:
    """Test MahlifConfig default values."""
    config = MahlifConfig()
    assert isinstance(config.sibelius, SibeliusConfig)
