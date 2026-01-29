"""Sibelius automation via AppleScript with state machine."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


# =============================================================================
# Core AppleScript execution
# =============================================================================


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


# =============================================================================
# UI State Detection
# =============================================================================


class ModalType(Enum):
    """Known modal dialog types."""

    NONE = "none"
    QUICK_START = "quick_start"
    EDIT_PLUGINS = "edit_plugins"
    MESSAGE_BOX = "message_box"
    SAVE_CHANGES = "save_changes"
    UNKNOWN = "unknown"


@dataclass
class UIState:
    """Current Sibelius UI state."""

    windows: list[str]
    front_window: str
    modal: ModalType
    score_open: bool
    bar_count: int
    command_search_active: bool

    def __str__(self) -> str:
        """Human-readable state description."""
        parts = []
        if self.modal != ModalType.NONE:
            parts.append(f"modal={self.modal.value}")
        if self.score_open:
            parts.append(f"score_open (bars={self.bar_count})")
        else:
            parts.append("no_score")
        if self.command_search_active:
            parts.append("cmd_search")
        return f"UIState({', '.join(parts)})"


def get_windows() -> list[str]:
    """Get list of all Sibelius window names."""
    result = run_applescript("""
        tell application "System Events"
            tell process "Sibelius"
                return name of every window
            end tell
        end tell
    """)
    if not result:
        return []
    return [w.strip() for w in result.split(",")]


def get_front_window() -> str:
    """Get name of front window."""
    try:
        return run_applescript("""
            tell application "System Events"
                tell process "Sibelius"
                    return name of front window
                end tell
            end tell
        """)
    except RuntimeError:
        return ""


def detect_modal() -> ModalType:
    """Detect what modal dialog (if any) is open."""
    windows = get_windows()
    front = get_front_window()

    # Check for known modals by window name
    if "Quick Start" in windows:
        return ModalType.QUICK_START
    if "Edit Plugins" in front or "Edit Plug-ins" in front:
        return ModalType.EDIT_PLUGINS

    # Check for message box (Sibelius dialog with specific structure)
    try:
        # Message boxes have a specific structure with static text and OK button
        result = run_applescript("""
            tell application "System Events"
                tell process "Sibelius"
                    if exists (front window) then
                        set winName to name of front window
                        if winName is "Sibelius" then
                            -- Check if it looks like a message box
                            if exists (static text 1 of front window) then
                                return "message_box"
                            end if
                        end if
                    end if
                end tell
            end tell
            return "none"
        """)
        if result == "message_box":
            return ModalType.MESSAGE_BOX
    except RuntimeError:
        pass

    # Check for save changes sheet
    try:
        result = run_applescript("""
            tell application "System Events"
                tell process "Sibelius"
                    if exists (sheet 1 of front window) then
                        return "save_changes"
                    end if
                end tell
            end tell
            return "none"
        """)
        if result == "save_changes":
            return ModalType.SAVE_CHANGES
    except RuntimeError:
        pass

    return ModalType.NONE


def is_score_open() -> bool:
    """Check if a score is currently open."""
    front = get_front_window()
    # Score windows typically have "untitled" or a filename
    # Quick Start and other dialogs have specific names
    if not front:
        return False
    if front in ("Sibelius", "Quick Start", "Edit Plugins"):
        return False
    # Score windows show in title bar
    return True


def get_bar_count() -> int:
    """Get bar count from status bar (returns 0 if can't determine)."""
    # This is tricky - we can't easily read the status bar via accessibility
    # For now, return -1 to indicate unknown
    # TODO: Could potentially use OCR or other methods
    return -1


def is_command_search_active() -> bool:
    """Check if command search dropdown is active."""
    try:
        # Command search shows as a combo box in the toolbar
        result = run_applescript("""
            tell application "System Events"
                tell process "Sibelius"
                    -- Check if any combo box is focused
                    set focusedElement to focused of front window
                    return focusedElement as string
                end tell
            end tell
        """)
        return "combo" in result.lower() or "search" in result.lower()
    except RuntimeError:
        return False


def get_ui_state() -> UIState:
    """Get comprehensive UI state."""
    windows = get_windows()
    front = get_front_window()
    modal = detect_modal()
    score_open = is_score_open() and modal == ModalType.NONE
    bar_count = get_bar_count() if score_open else 0
    cmd_search = is_command_search_active()

    return UIState(
        windows=windows,
        front_window=front,
        modal=modal,
        score_open=score_open,
        bar_count=bar_count,
        command_search_active=cmd_search,
    )


# =============================================================================
# State Transitions / Actions
# =============================================================================


def activate() -> None:
    """Bring Sibelius to front."""
    run_applescript("""
        tell application "Sibelius"
            activate
        end tell
        delay 0.3
    """)


def press_key(key: str, modifiers: list[str] | None = None) -> None:
    """Press a key with optional modifiers.

    Args:
        key: Key to press (letter, or "return", "escape", "tab", etc.)
        modifiers: List of modifiers ("command", "control", "option", "shift")
    """
    if modifiers:
        mod_str = ", ".join(f"{m} down" for m in modifiers)
        mod_clause = f" using {{{mod_str}}}"
    else:
        mod_clause = ""

    # Map special keys to key codes
    key_codes = {
        "return": "36",
        "escape": "53",
        "tab": "48",
        "delete": "51",
        "home": "115",
        "end": "119",
        "up": "126",
        "down": "125",
        "left": "123",
        "right": "124",
    }

    if key.lower() in key_codes:
        run_applescript(f"""
            tell application "System Events"
                tell process "Sibelius"
                    key code {key_codes[key.lower()]}{mod_clause}
                    delay 0.2
                end tell
            end tell
        """)
    else:
        run_applescript(f"""
            tell application "System Events"
                tell process "Sibelius"
                    keystroke "{key}"{mod_clause}
                    delay 0.2
                end tell
            end tell
        """)


def type_text(text: str, delay: float = 0.1) -> None:
    """Type text into the current field."""
    # Escape special characters for AppleScript
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    run_applescript(f"""
        tell application "System Events"
            tell process "Sibelius"
                keystroke "{escaped}"
                delay {delay}
            end tell
        end tell
    """)


def type_in_field(text: str, delay: float = 0.1) -> None:
    """Select all and type text, replacing any existing content.

    NOTE: Assumes the field already has focus. Caller must ensure focus first.
    Some dialogs auto-focus fields (e.g., Edit Plug-ins Find box),
    others require explicit focus (e.g., Quick Start search).
    """
    press_key("a", ["command"])  # Select all
    run_applescript("delay 0.1")
    type_text(text, delay)  # Typing replaces selection


def click_button(button_name: str, window: str = "front window") -> bool:
    """Click a button by name. Returns True if successful."""
    try:
        run_applescript(f"""
            tell application "System Events"
                tell process "Sibelius"
                    click button "{button_name}" of {window}
                    delay 0.3
                end tell
            end tell
        """)
        return True
    except RuntimeError:
        return False


def click_button_in_group(button_name: str) -> bool:
    """Click a button that's inside a group (like Close in Edit Plugins)."""
    try:
        run_applescript(f"""
            tell application "System Events"
                tell process "Sibelius"
                    repeat with g in groups of front window
                        try
                            click button "{button_name}" of g
                            exit repeat
                        end try
                    end repeat
                    delay 0.3
                end tell
            end tell
        """)
        return True
    except RuntimeError:
        return False


# =============================================================================
# Modal Dismissal
# =============================================================================


def dismiss_message_box() -> bool:
    """Dismiss a message box by pressing Enter."""
    press_key("return")
    run_applescript("delay 0.3")
    return detect_modal() != ModalType.MESSAGE_BOX


def dismiss_save_changes(save: bool = False) -> bool:
    """Dismiss save changes dialog."""
    if save:
        click_button("Save")
    else:
        click_button("Don't Save")
    run_applescript("delay 0.3")
    return detect_modal() != ModalType.SAVE_CHANGES


def dismiss_quick_start() -> bool:
    """Dismiss Quick Start by clicking Close button."""
    # Escape doesn't work on Quick Start - must click Close button
    click_button("Close")
    run_applescript("delay 0.5")
    return detect_modal() != ModalType.QUICK_START


def dismiss_edit_plugins() -> bool:
    """Dismiss Edit Plugins dialog."""
    click_button_in_group("Close")
    run_applescript("delay 0.3")
    return detect_modal() != ModalType.EDIT_PLUGINS


def dismiss_current_modal() -> bool:
    """Dismiss whatever modal is currently showing.

    Returns True if a modal was dismissed, False if no modal was open.
    """
    modal = detect_modal()
    match modal:
        case ModalType.NONE:
            return False
        case ModalType.MESSAGE_BOX:
            return dismiss_message_box()
        case ModalType.SAVE_CHANGES:
            return dismiss_save_changes(save=False)
        case ModalType.QUICK_START:
            return dismiss_quick_start()
        case ModalType.EDIT_PLUGINS:
            return dismiss_edit_plugins()
        case ModalType.UNKNOWN:
            # Try Enter then Escape
            press_key("return")
            run_applescript("delay 0.3")
            if detect_modal() == ModalType.UNKNOWN:
                press_key("escape")
                run_applescript("delay 0.3")
            return True
        case _:  # pragma: no cover
            raise TypeError(f"Unknown modal type: {modal}")


def dismiss_all_modals(max_attempts: int = 5) -> int:
    """Dismiss all open modals.

    Returns count of modals dismissed.
    """
    count = 0
    for _ in range(max_attempts):
        if not dismiss_current_modal():
            break
        count += 1
    return count


# =============================================================================
# Command Search
# =============================================================================


def open_command_search() -> None:
    """Open the command search dropdown (Ctrl+0)."""
    press_key("0", ["control"])
    run_applescript("delay 1")


def close_command_search() -> None:
    """Close command search dropdown if open.

    Note: This doesn't clear the text. Use type_in_field() when typing
    in the command search to handle any leftover text.
    """
    activate()
    press_key("escape")
    run_applescript("delay 0.3")


def run_command(command: str, arrow_down: int = 0) -> None:
    """Run a command via command search.

    Args:
        command: Command text to search for
        arrow_down: Number of times to press down arrow before Enter
                   (to select non-first result)
    """
    open_command_search()
    type_in_field(command)  # Clear any leftover text first
    run_applescript("delay 0.8")
    for _ in range(arrow_down):
        press_key("down")
        run_applescript("delay 0.2")
    press_key("return")
    run_applescript("delay 0.5")


# =============================================================================
# Score Management
# =============================================================================


def close_score(save: bool = False) -> None:
    """Close current score."""
    activate()
    press_key("w", ["command"])
    run_applescript("delay 0.5")
    modal = detect_modal()
    if modal == ModalType.SAVE_CHANGES:
        dismiss_save_changes(save=save)


def create_blank_score() -> bool:
    """Create a new blank score from any state.

    Returns True if successful.
    """
    activate()

    # First, ensure we're in a clean state
    dismiss_all_modals()

    # Open Quick Start
    press_key("n", ["command"])
    run_applescript("delay 2")

    # Check if Quick Start opened
    if detect_modal() != ModalType.QUICK_START:
        return False

    # Focus the search field in Quick Start
    run_applescript("""
        tell application "System Events"
            tell process "Sibelius"
                tell window "Quick Start"
                    set focused of text field 1 of group 2 to true
                end tell
            end tell
        end tell
    """)
    run_applescript("delay 0.3")

    # Search for Blank, Tab into results, Enter to select
    type_in_field("Blank")
    run_applescript("delay 0.5")
    press_key("tab")
    run_applescript("delay 0.3")
    press_key("return")
    run_applescript("delay 3")

    # Verify score was created
    return is_score_open()


def ensure_blank_score() -> bool:
    """Ensure we have a blank score open, creating one if needed.

    Returns True if we end up with a blank score.
    """
    # Make sure Sibelius is active
    activate()

    # Dismiss any modals first
    dismiss_all_modals()

    # If a score is open, close it
    if is_score_open():
        close_score(save=False)
        dismiss_all_modals()

    # Now create a blank score
    return create_blank_score()


# =============================================================================
# Plugin Management
# =============================================================================


def reload_plugin(plugin_menu_name: str) -> bool:
    """Reload a plugin via Edit Plugins dialog.

    Args:
        plugin_menu_name: The menu name (e.g., "Mahlif: Import Test")

    Returns True if successful.
    """
    print(f"→ Reloading plugin: {plugin_menu_name}")

    # Ensure we're in a clean state
    dismiss_all_modals()
    close_command_search()

    # Open Edit Plug-ins via command search
    run_command("Edit Plug-ins")
    run_applescript("delay 1.5")

    # Verify dialog opened
    if detect_modal() != ModalType.EDIT_PLUGINS:
        # Try to detect by window name
        if "Edit Plugins" not in get_front_window():
            print("  ✗ Failed to open Edit Plugins dialog")
            return False

    # Search for plugin - Enter finds and selects the match
    type_in_field(plugin_menu_name)
    run_applescript("delay 0.5")
    press_key("return")
    run_applescript("delay 0.5")

    # Click Unload
    if not click_button("&Unload"):
        print("  ✗ Failed to click Unload")
        dismiss_edit_plugins()
        return False
    run_applescript("delay 0.5")

    # Click Reload
    if not click_button("&Reload"):
        print("  ✗ Failed to click Reload")
        dismiss_edit_plugins()
        return False
    run_applescript("delay 1")

    # Close dialog
    dismiss_edit_plugins()
    print("  ✓ Plugin reloaded")
    return True


def run_plugin(plugin_menu_name: str, arrow_down: int = 0) -> tuple[bool, str]:
    """Run a plugin via command search.

    Args:
        plugin_menu_name: The menu name (e.g., "Mahlif: Import Test")
        arrow_down: Number of times to press down arrow before Enter
                   (usually 0, but may need 1 if multiple matches)

    Returns:
        (success, message) tuple. If error, message contains error text.
    """
    print(f"→ Running plugin: {plugin_menu_name}")

    # Ensure clean state
    dismiss_all_modals()
    close_command_search()

    # Run via command search
    run_command(plugin_menu_name, arrow_down=arrow_down)
    run_applescript("delay 5")

    # Handle completion/error modals
    errors: list[str] = []
    max_modals = 5  # Safety limit
    for _ in range(max_modals):
        if detect_modal() != ModalType.MESSAGE_BOX:
            break

        # Get message text from the modal
        try:
            msg = run_applescript("""
                tell application "System Events"
                    tell process "Sibelius"
                        get value of static text 1 of front window
                    end tell
                end tell
            """)
            if msg and "error" in msg.lower():
                errors.append(msg)
                print(f"  ✗ Plugin error: {msg}")
            else:
                print(f"  ✓ {msg}")
        except RuntimeError:
            pass

        # Dismiss this modal
        press_key("return")
        run_applescript("delay 0.5")

    if errors:
        return False, "\n".join(errors)
    return True, ""


# =============================================================================
# Navigation
# =============================================================================


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


def go_to_page(page_num: int) -> None:
    """Navigate to specific page."""
    print(f"→ Going to page {page_num}")
    run_command("Go to Page")
    run_applescript("delay 0.5")
    type_text(str(page_num))
    press_key("return")
    run_applescript("delay 1")


def scroll_to_start() -> None:
    """Scroll to beginning of score."""
    press_key("home", ["command"])
    run_applescript("delay 0.3")


# =============================================================================
# Window Management
# =============================================================================


def list_windows() -> list[str]:
    """List all open Sibelius windows."""
    return get_windows()


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


# =============================================================================
# Screenshots & Utilities
# =============================================================================


def screenshot(save_path: str | Path) -> Path:
    """Take screenshot and save to path."""
    path = Path(save_path)
    run_applescript(f'do shell script "screencapture -x {path}"')
    return path


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
    run_applescript("""
        tell application "Visual Studio Code"
            activate
        end tell
    """)


# =============================================================================
# Legacy compatibility (deprecated, use new functions)
# =============================================================================


def dismiss_modal(count: int = 1) -> None:
    """Dismiss modal dialog(s) by pressing Enter.

    DEPRECATED: Use dismiss_all_modals() or dismiss_current_modal() instead.
    """
    for _ in range(count):
        press_key("return")
        run_applescript("delay 0.5")


def close_without_saving() -> None:
    """Close current score without saving.

    DEPRECATED: Use close_score(save=False) instead.
    """
    close_score(save=False)


def new_blank_score() -> None:
    """Create new blank score.

    DEPRECATED: Use ensure_blank_score() instead.
    """
    create_blank_score()


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
