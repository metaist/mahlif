"""Sibelius automation via AppleScript."""

from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_applescript(script: str) -> str:
    """Run AppleScript and return output."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript error: {result.stderr}")
    return result.stdout.strip()


def activate() -> None:
    """Bring Sibelius to front."""
    run_applescript("""
        tell application "Sibelius"
            activate
        end tell
        delay 0.3
    """)


def list_windows() -> list[str]:
    """List all open Sibelius windows."""
    result = run_applescript("""
        tell application "System Events"
            tell process "Sibelius"
                return name of every window
            end tell
        end tell
    """)
    # Parse AppleScript list format
    if not result:
        return []
    return [w.strip() for w in result.split(",")]


def switch_to_window(partial_name: str) -> bool:
    """Switch to window matching partial name."""
    script = f"""
        tell application "System Events"
            tell process "Sibelius"
                set windowMenuItems to name of every menu item of menu "Window" of menu bar 1
                repeat with i from 1 to count of windowMenuItems
                    set itemName to item i of windowMenuItems
                    if itemName is not missing value then
                        if itemName contains "{partial_name}" then
                            click menu item i of menu "Window" of menu bar 1
                            delay 0.3
                            return "true"
                        end if
                    end if
                end repeat
            end tell
        end tell
        return "false"
    """
    return run_applescript(script) == "true"


def screenshot(save_path: str | Path) -> Path:
    """Take screenshot and save to path."""
    path = Path(save_path)
    run_applescript(f'do shell script "screencapture -x {path}"')
    return path


def go_to_bar(bar_num: int) -> None:
    """Navigate to specific bar."""
    run_applescript(f"""
        tell application "System Events"
            tell process "Sibelius"
                keystroke "g" using {{command down, option down}}
                delay 0.3
                keystroke "{bar_num}"
                delay 0.1
                keystroke return
                delay 0.3
            end tell
        end tell
    """)


def notify(message: str) -> None:
    """Show macOS notification."""
    run_applescript(f'display notification "{message}" with title "Mahlif Automation"')


def say(message: str) -> None:
    """Speak message aloud."""
    run_applescript(f'say "{message}"')


def starting(task: str = "automation") -> None:
    """Signal automation is starting."""
    print(f"▶ Starting: {task}")
    notify(f"Starting: {task}")
    say(f"Starting {task}")
    run_applescript("delay 1.5")


def done() -> None:
    """Signal automation is complete and switch back to VS Code."""
    print("✓ Done")
    notify("Automation complete")
    say("Done")
    # Switch back to VS Code so user can see terminal
    run_applescript("""
        tell application "Visual Studio Code"
            activate
        end tell
    """)


def go_to_page(page_num: int) -> None:
    """Navigate to specific page via Sibelius Command Search (Ctrl+0)."""
    print(f"→ Going to page {page_num}")
    notify(f"Going to page {page_num}")
    run_applescript(f"""
        tell application "System Events"
            tell process "Sibelius"
                -- Open Sibelius Command Search (Ctrl+0)
                keystroke "0" using control down
                delay 1
                keystroke "Go to Page"
                delay 0.5
                keystroke return
                delay 0.5
                keystroke "{page_num}"
                delay 0.3
                keystroke return
                delay 3
            end tell
        end tell
    """)


def new_blank_score() -> None:
    """Create new blank score."""
    run_applescript("""
        tell application "System Events"
            tell process "Sibelius"
                keystroke "n" using command down
                delay 0.5
                keystroke return
                delay 1
            end tell
        end tell
    """)


def close_without_saving() -> None:
    """Close current score without saving."""
    run_applescript("""
        tell application "System Events"
            tell process "Sibelius"
                keystroke "w" using command down
                delay 0.3
                try
                    click button "Don't Save" of sheet 1 of window 1
                end try
                delay 0.3
            end tell
        end tell
    """)


def scroll_to_start() -> None:
    """Scroll to beginning of score."""
    run_applescript("""
        tell application "System Events"
            tell process "Sibelius"
                key code 115 using command down
                delay 0.3
            end tell
        end tell
    """)


def run_plugin(plugin_name: str) -> None:
    """Run a plugin from the Other menu."""
    run_applescript(f"""
        tell application "System Events"
            tell process "Sibelius"
                click menu item "{plugin_name}" of menu "Other" of menu item "Other" of menu "Plug-ins" of menu bar 1
                delay 0.5
            end tell
        end tell
    """)


def compare_windows(
    name1: str,
    name2: str,
    output_dir: str | Path,
    page: int = 1,
) -> tuple[Path, Path]:
    """Screenshot two windows at same page for comparison."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    activate()

    # First window
    switch_to_window(name1)
    go_to_page(page)
    path1 = screenshot(output_dir / f"{name1.replace(' ', '_')}_p{page}.png")

    # Second window
    switch_to_window(name2)
    go_to_page(page)
    path2 = screenshot(output_dir / f"{name2.replace(' ', '_')}_p{page}.png")

    return path1, path2
