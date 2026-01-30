"""Tests for main entry point of convert module."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from mahlif.sibelius.convert import main as generate_main


def test_generate_main_no_args() -> None:
    """Test main with no arguments."""
    with patch.object(sys, "argv", ["convert.py"]):
        assert generate_main() == 1


def test_generate_main_missing_file() -> None:
    """Test main with missing input file."""
    with patch.object(sys, "argv", ["convert.py", "nonexistent.xml", "out.plg"]):
        assert generate_main() == 1


def test_generate_main_success() -> None:
    """Test main with valid input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = Path(tmpdir) / "test.mahlif.xml"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
<meta><work-title>Test</work-title></meta>
<layout/>
<movement>
    <system-staff/>
    <staff n="1" instrument="Flute">
        <bar n="1" length="1024"/>
    </staff>
</movement>
</mahlif>"""
        xml_path.write_text(xml_content, encoding="utf-8")

        out_path = Path(tmpdir) / "test.plg"
        with patch.object(sys, "argv", ["convert.py", str(xml_path), str(out_path)]):
            result = generate_main()
            assert result == 0
            assert out_path.exists()


def test_convert_cli_with_title_from_meta() -> None:
    """Test CLI uses work_title when available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = Path(tmpdir) / "test.mahlif.xml"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mahlif>
<meta><work-title>My Symphony</work-title></meta>
<layout/>
<movement>
    <system-staff/>
    <staff n="1" instrument="Flute">
        <bar n="1" length="1024"/>
    </staff>
</movement>
</mahlif>"""
        xml_path.write_text(xml_content, encoding="utf-8")
        out_path = Path(tmpdir) / "test.plg"
        with patch.object(sys, "argv", ["convert.py", str(xml_path), str(out_path)]):
            result = generate_main()
            assert result == 0
