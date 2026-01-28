#!/usr/bin/env python3
"""Compare original and imported scores visually."""

from __future__ import annotations

import sys
from pathlib import Path

from mahlif.sibelius.automation import (
    activate,
    compare_windows,
    list_windows,
    screenshot,
    switch_to_window,
    go_to_page,
    scroll_to_start,
)


def main() -> int:
    """Main entry point."""
    output_dir = Path("/tmp/sibelius_compare")
    output_dir.mkdir(exist_ok=True)

    activate()
    windows = list_windows()
    print(f"Open windows: {windows}")

    # Find original and import windows
    original = None
    imported = None
    for w in windows:
        if "untitled" in w.lower():
            imported = w
        elif "8740" in w:  # Original file pattern
            original = w

    if not original or not imported:
        print(f"Need both original and imported windows open")
        print(f"  Original: {original}")
        print(f"  Imported: {imported}")
        return 1

    # Compare page 1
    print("Comparing page 1...")
    switch_to_window("untitled")
    scroll_to_start()
    screenshot(output_dir / "imported_p1.png")

    switch_to_window("8740")
    scroll_to_start()
    screenshot(output_dir / "original_p1.png")

    print(f"Screenshots saved to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
