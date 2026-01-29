"""Tests for Sibelius automation module."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Core AppleScript
# =============================================================================


def test_run_applescript_success() -> None:
    """Test successful AppleScript execution."""
    from mahlif.sibelius.automation import run_applescript

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = ""

    with patch.object(subprocess, "run", return_value=mock_result):
        result = run_applescript("test script")
        assert result == "output"


def test_run_applescript_error() -> None:
    """Test AppleScript error handling."""
    from mahlif.sibelius.automation import run_applescript

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error message"

    with patch.object(subprocess, "run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="AppleScript error"):
            run_applescript("test script")


# =============================================================================
# UI State Detection
# =============================================================================


def test_modal_type_enum() -> None:
    """Test ModalType enum values."""
    from mahlif.sibelius.automation import ModalType

    assert ModalType.NONE.value == "none"
    assert ModalType.QUICK_START.value == "quick_start"
    assert ModalType.EDIT_PLUGINS.value == "edit_plugins"
    assert ModalType.MESSAGE_BOX.value == "message_box"
    assert ModalType.SAVE_CHANGES.value == "save_changes"
    assert ModalType.UNKNOWN.value == "unknown"


def test_ui_state_str() -> None:
    """Test UIState string representation."""
    from mahlif.sibelius.automation import ModalType, UIState

    state = UIState(
        windows=["Test"],
        front_window="Test",
        modal=ModalType.NONE,
        score_open=True,
        bar_count=4,
        command_search_active=False,
    )
    assert "score_open" in str(state)
    assert "bars=4" in str(state)

    state2 = UIState(
        windows=[],
        front_window="",
        modal=ModalType.MESSAGE_BOX,
        score_open=False,
        bar_count=0,
        command_search_active=True,
    )
    assert "modal=message_box" in str(state2)
    assert "no_score" in str(state2)
    assert "cmd_search" in str(state2)


def test_get_windows_empty() -> None:
    """Test get_windows with no windows."""
    from mahlif.sibelius.automation import get_windows

    with patch("mahlif.sibelius.automation.run_applescript", return_value=""):
        result = get_windows()
        assert result == []


def test_get_windows_multiple() -> None:
    """Test get_windows with multiple windows."""
    from mahlif.sibelius.automation import get_windows

    with patch(
        "mahlif.sibelius.automation.run_applescript",
        return_value="Window 1, Window 2",
    ):
        result = get_windows()
        assert result == ["Window 1", "Window 2"]


def test_get_front_window() -> None:
    """Test get_front_window."""
    from mahlif.sibelius.automation import get_front_window

    with patch("mahlif.sibelius.automation.run_applescript", return_value="untitled 1"):
        result = get_front_window()
        assert result == "untitled 1"


def test_get_front_window_error() -> None:
    """Test get_front_window when no window."""
    from mahlif.sibelius.automation import get_front_window

    with patch(
        "mahlif.sibelius.automation.run_applescript",
        side_effect=RuntimeError("no window"),
    ):
        result = get_front_window()
        assert result == ""


def test_detect_modal_none() -> None:
    """Test detect_modal when no modal."""
    from mahlif.sibelius.automation import ModalType, detect_modal

    with patch("mahlif.sibelius.automation.get_windows", return_value=["untitled"]):
        with patch(
            "mahlif.sibelius.automation.get_front_window", return_value="untitled"
        ):
            with patch(
                "mahlif.sibelius.automation.run_applescript", return_value="none"
            ):
                result = detect_modal()
                assert result == ModalType.NONE


def test_detect_modal_quick_start() -> None:
    """Test detect_modal for Quick Start."""
    from mahlif.sibelius.automation import ModalType, detect_modal

    with patch(
        "mahlif.sibelius.automation.get_windows",
        return_value=["Sibelius", "Quick Start"],
    ):
        with patch(
            "mahlif.sibelius.automation.get_front_window",
            return_value="Quick Start",
        ):
            result = detect_modal()
            assert result == ModalType.QUICK_START


def test_detect_modal_edit_plugins() -> None:
    """Test detect_modal for Edit Plugins."""
    from mahlif.sibelius.automation import ModalType, detect_modal

    with patch("mahlif.sibelius.automation.get_windows", return_value=["Edit Plugins"]):
        with patch(
            "mahlif.sibelius.automation.get_front_window",
            return_value="Edit Plugins",
        ):
            result = detect_modal()
            assert result == ModalType.EDIT_PLUGINS


def test_detect_modal_message_box() -> None:
    """Test detect_modal for message box."""
    from mahlif.sibelius.automation import ModalType, detect_modal

    with patch("mahlif.sibelius.automation.get_windows", return_value=["Sibelius"]):
        with patch(
            "mahlif.sibelius.automation.get_front_window", return_value="Sibelius"
        ):
            with patch(
                "mahlif.sibelius.automation.run_applescript",
                side_effect=["message_box", "none"],
            ):
                result = detect_modal()
                assert result == ModalType.MESSAGE_BOX


def test_detect_modal_save_changes() -> None:
    """Test detect_modal for save changes sheet."""
    from mahlif.sibelius.automation import ModalType, detect_modal

    with patch("mahlif.sibelius.automation.get_windows", return_value=["untitled"]):
        with patch(
            "mahlif.sibelius.automation.get_front_window", return_value="untitled"
        ):
            with patch(
                "mahlif.sibelius.automation.run_applescript",
                side_effect=["none", "save_changes"],
            ):
                result = detect_modal()
                assert result == ModalType.SAVE_CHANGES


def test_detect_modal_applescript_error() -> None:
    """Test detect_modal handles AppleScript errors."""
    from mahlif.sibelius.automation import ModalType, detect_modal

    with patch("mahlif.sibelius.automation.get_windows", return_value=["untitled"]):
        with patch(
            "mahlif.sibelius.automation.get_front_window", return_value="untitled"
        ):
            with patch(
                "mahlif.sibelius.automation.run_applescript",
                side_effect=RuntimeError("error"),
            ):
                result = detect_modal()
                assert result == ModalType.NONE


def test_is_score_open_true() -> None:
    """Test is_score_open when score is open."""
    from mahlif.sibelius.automation import is_score_open

    with patch(
        "mahlif.sibelius.automation.get_front_window", return_value="untitled 1"
    ):
        assert is_score_open() is True


def test_is_score_open_false_no_window() -> None:
    """Test is_score_open with no window."""
    from mahlif.sibelius.automation import is_score_open

    with patch("mahlif.sibelius.automation.get_front_window", return_value=""):
        assert is_score_open() is False


def test_is_score_open_false_quick_start() -> None:
    """Test is_score_open when Quick Start showing."""
    from mahlif.sibelius.automation import is_score_open

    with patch(
        "mahlif.sibelius.automation.get_front_window", return_value="Quick Start"
    ):
        assert is_score_open() is False


def test_get_bar_count() -> None:
    """Test get_bar_count returns -1 (unknown)."""
    from mahlif.sibelius.automation import get_bar_count

    assert get_bar_count() == -1


def test_is_command_search_active_false() -> None:
    """Test is_command_search_active when not active."""
    from mahlif.sibelius.automation import is_command_search_active

    with patch("mahlif.sibelius.automation.run_applescript", return_value="false"):
        assert is_command_search_active() is False


def test_is_command_search_active_true() -> None:
    """Test is_command_search_active when active."""
    from mahlif.sibelius.automation import is_command_search_active

    with patch("mahlif.sibelius.automation.run_applescript", return_value="combo box"):
        assert is_command_search_active() is True


def test_is_command_search_active_error() -> None:
    """Test is_command_search_active handles errors."""
    from mahlif.sibelius.automation import is_command_search_active

    with patch(
        "mahlif.sibelius.automation.run_applescript",
        side_effect=RuntimeError("error"),
    ):
        assert is_command_search_active() is False


def test_get_ui_state() -> None:
    """Test get_ui_state combines all state."""
    from mahlif.sibelius.automation import ModalType, get_ui_state

    with patch("mahlif.sibelius.automation.get_windows", return_value=["untitled 1"]):
        with patch(
            "mahlif.sibelius.automation.get_front_window", return_value="untitled 1"
        ):
            with patch(
                "mahlif.sibelius.automation.detect_modal", return_value=ModalType.NONE
            ):
                with patch(
                    "mahlif.sibelius.automation.is_command_search_active",
                    return_value=False,
                ):
                    state = get_ui_state()
                    assert state.windows == ["untitled 1"]
                    assert state.front_window == "untitled 1"
                    assert state.modal == ModalType.NONE
                    assert state.score_open is True


# =============================================================================
# State Transitions / Actions
# =============================================================================


def test_activate() -> None:
    """Test activate function."""
    from mahlif.sibelius.automation import activate

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        activate()
        mock.assert_called_once()
        assert "Sibelius" in mock.call_args[0][0]


def test_press_key_letter() -> None:
    """Test press_key with a letter."""
    from mahlif.sibelius.automation import press_key

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        press_key("a")
        assert 'keystroke "a"' in mock.call_args[0][0]


def test_press_key_with_modifiers() -> None:
    """Test press_key with modifiers."""
    from mahlif.sibelius.automation import press_key

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        press_key("n", ["command"])
        assert "command down" in mock.call_args[0][0]


def test_press_key_special() -> None:
    """Test press_key with special key."""
    from mahlif.sibelius.automation import press_key

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        press_key("return")
        assert "key code 36" in mock.call_args[0][0]


def test_press_key_escape() -> None:
    """Test press_key with escape."""
    from mahlif.sibelius.automation import press_key

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        press_key("escape")
        assert "key code 53" in mock.call_args[0][0]


def test_press_key_arrows() -> None:
    """Test press_key with arrow keys."""
    from mahlif.sibelius.automation import press_key

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        press_key("down")
        assert "key code 125" in mock.call_args[0][0]

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        press_key("up")
        assert "key code 126" in mock.call_args[0][0]


def test_type_text() -> None:
    """Test type_text function."""
    from mahlif.sibelius.automation import type_text

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        type_text("hello")
        assert 'keystroke "hello"' in mock.call_args[0][0]


def test_type_text_escapes_special() -> None:
    """Test type_text escapes special characters."""
    from mahlif.sibelius.automation import type_text

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        type_text('test"quote')
        assert '\\"' in mock.call_args[0][0]


def test_click_button_success() -> None:
    """Test click_button succeeds."""
    from mahlif.sibelius.automation import click_button

    with patch("mahlif.sibelius.automation.run_applescript"):
        result = click_button("OK")
        assert result is True


def test_click_button_failure() -> None:
    """Test click_button fails gracefully."""
    from mahlif.sibelius.automation import click_button

    with patch(
        "mahlif.sibelius.automation.run_applescript",
        side_effect=RuntimeError("not found"),
    ):
        result = click_button("NonExistent")
        assert result is False


def test_click_button_in_group() -> None:
    """Test click_button_in_group."""
    from mahlif.sibelius.automation import click_button_in_group

    with patch("mahlif.sibelius.automation.run_applescript"):
        result = click_button_in_group("Close")
        assert result is True


# =============================================================================
# Modal Dismissal
# =============================================================================


def test_dismiss_message_box() -> None:
    """Test dismiss_message_box."""
    from mahlif.sibelius.automation import ModalType, dismiss_message_box

    with patch("mahlif.sibelius.automation.press_key"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.NONE,
            ):
                result = dismiss_message_box()
                assert result is True


def test_dismiss_save_changes_dont_save() -> None:
    """Test dismiss_save_changes without saving."""
    from mahlif.sibelius.automation import ModalType, dismiss_save_changes

    with patch("mahlif.sibelius.automation.click_button"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.NONE,
            ):
                result = dismiss_save_changes(save=False)
                assert result is True


def test_dismiss_save_changes_save() -> None:
    """Test dismiss_save_changes with saving."""
    from mahlif.sibelius.automation import ModalType, dismiss_save_changes

    with patch("mahlif.sibelius.automation.click_button") as mock_click:
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.NONE,
            ):
                dismiss_save_changes(save=True)
                mock_click.assert_called_with("Save")


def test_dismiss_quick_start() -> None:
    """Test dismiss_quick_start."""
    from mahlif.sibelius.automation import ModalType, dismiss_quick_start

    with patch("mahlif.sibelius.automation.press_key"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.NONE,
            ):
                result = dismiss_quick_start()
                assert result is True


def test_dismiss_edit_plugins() -> None:
    """Test dismiss_edit_plugins."""
    from mahlif.sibelius.automation import ModalType, dismiss_edit_plugins

    with patch("mahlif.sibelius.automation.click_button_in_group"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.NONE,
            ):
                result = dismiss_edit_plugins()
                assert result is True


def test_dismiss_current_modal_none() -> None:
    """Test dismiss_current_modal when no modal."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    with patch("mahlif.sibelius.automation.detect_modal", return_value=ModalType.NONE):
        result = dismiss_current_modal()
        assert result is False


def test_dismiss_current_modal_unknown() -> None:
    """Test dismiss_current_modal with unknown modal."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    call_count = [0]

    def mock_detect() -> ModalType:
        call_count[0] += 1
        if call_count[0] == 1:
            return ModalType.UNKNOWN
        return ModalType.NONE

    with patch("mahlif.sibelius.automation.detect_modal", side_effect=mock_detect):
        with patch("mahlif.sibelius.automation.press_key"):
            with patch("mahlif.sibelius.automation.run_applescript"):
                result = dismiss_current_modal()
                assert result is True


def test_dismiss_current_modal_unknown_needs_escape() -> None:
    """Test dismiss_current_modal unknown modal needs escape."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    call_count = [0]

    def mock_detect() -> ModalType:
        call_count[0] += 1
        if call_count[0] <= 2:
            return ModalType.UNKNOWN
        return ModalType.NONE

    with patch("mahlif.sibelius.automation.detect_modal", side_effect=mock_detect):
        with patch("mahlif.sibelius.automation.press_key") as mock_press:
            with patch("mahlif.sibelius.automation.run_applescript"):
                dismiss_current_modal()
                calls = [c[0][0] for c in mock_press.call_args_list]
                assert "return" in calls
                assert "escape" in calls


def test_dismiss_all_modals() -> None:
    """Test dismiss_all_modals dismisses multiple."""
    from mahlif.sibelius.automation import dismiss_all_modals

    call_count = [0]

    def mock_dismiss() -> bool:
        call_count[0] += 1
        return call_count[0] <= 3

    with patch(
        "mahlif.sibelius.automation.dismiss_current_modal", side_effect=mock_dismiss
    ):
        count = dismiss_all_modals()
        assert count == 3


def test_dismiss_all_modals_max_attempts() -> None:
    """Test dismiss_all_modals respects max attempts."""
    from mahlif.sibelius.automation import dismiss_all_modals

    with patch("mahlif.sibelius.automation.dismiss_current_modal", return_value=True):
        count = dismiss_all_modals(max_attempts=2)
        assert count == 2


# =============================================================================
# Command Search
# =============================================================================


def test_open_command_search() -> None:
    """Test open_command_search."""
    from mahlif.sibelius.automation import open_command_search

    with patch("mahlif.sibelius.automation.press_key") as mock:
        with patch("mahlif.sibelius.automation.run_applescript"):
            open_command_search()
            mock.assert_called_with("0", ["control"])


def test_close_command_search() -> None:
    """Test close_command_search."""
    from mahlif.sibelius.automation import close_command_search

    with patch("mahlif.sibelius.automation.press_key") as mock:
        with patch("mahlif.sibelius.automation.run_applescript"):
            close_command_search()
            mock.assert_called_with("escape")


def test_run_command() -> None:
    """Test run_command."""
    from mahlif.sibelius.automation import run_command

    with patch("mahlif.sibelius.automation.open_command_search"):
        with patch("mahlif.sibelius.automation.type_text"):
            with patch("mahlif.sibelius.automation.press_key"):
                with patch("mahlif.sibelius.automation.run_applescript"):
                    run_command("Test Command")


def test_run_command_with_arrow_down() -> None:
    """Test run_command with arrow_down."""
    from mahlif.sibelius.automation import run_command

    with patch("mahlif.sibelius.automation.open_command_search"):
        with patch("mahlif.sibelius.automation.type_text"):
            with patch("mahlif.sibelius.automation.press_key") as mock_press:
                with patch("mahlif.sibelius.automation.run_applescript"):
                    run_command("Test", arrow_down=2)
                    down_calls = [
                        c for c in mock_press.call_args_list if c[0][0] == "down"
                    ]
                    assert len(down_calls) == 2


# =============================================================================
# Score Management
# =============================================================================


def test_close_score() -> None:
    """Test close_score without saving."""
    from mahlif.sibelius.automation import ModalType, close_score

    with patch("mahlif.sibelius.automation.press_key"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.NONE,
            ):
                close_score(save=False)


def test_close_score_with_save_dialog() -> None:
    """Test close_score handles save dialog."""
    from mahlif.sibelius.automation import ModalType, close_score

    with patch("mahlif.sibelius.automation.press_key"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch(
                "mahlif.sibelius.automation.detect_modal",
                return_value=ModalType.SAVE_CHANGES,
            ):
                with patch("mahlif.sibelius.automation.dismiss_save_changes") as mock:
                    close_score(save=False)
                    mock.assert_called_with(save=False)


def test_create_blank_score_success() -> None:
    """Test create_blank_score succeeds."""
    from mahlif.sibelius.automation import ModalType, create_blank_score

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.press_key"):
            with patch("mahlif.sibelius.automation.run_applescript"):
                with patch(
                    "mahlif.sibelius.automation.detect_modal",
                    return_value=ModalType.QUICK_START,
                ):
                    with patch(
                        "mahlif.sibelius.automation.is_score_open", return_value=True
                    ):
                        result = create_blank_score()
                        assert result is True


def test_create_blank_score_failure() -> None:
    """Test create_blank_score fails if Quick Start doesn't open."""
    from mahlif.sibelius.automation import ModalType, create_blank_score

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.press_key"):
            with patch("mahlif.sibelius.automation.run_applescript"):
                with patch(
                    "mahlif.sibelius.automation.detect_modal",
                    return_value=ModalType.NONE,
                ):
                    result = create_blank_score()
                    assert result is False


def test_ensure_blank_score_already_open() -> None:
    """Test ensure_blank_score when score already open."""
    from mahlif.sibelius.automation import ensure_blank_score

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.is_score_open", return_value=True):
            with patch("mahlif.sibelius.automation.close_score"):
                with patch(
                    "mahlif.sibelius.automation.create_blank_score",
                    return_value=True,
                ):
                    result = ensure_blank_score()
                    assert result is True


# =============================================================================
# Plugin Management
# =============================================================================


def test_reload_plugin_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test reload_plugin succeeds."""
    from mahlif.sibelius.automation import ModalType, reload_plugin

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.open_command_search"):
                with patch("mahlif.sibelius.automation.type_text"):
                    with patch("mahlif.sibelius.automation.press_key"):
                        with patch("mahlif.sibelius.automation.run_applescript"):
                            with patch(
                                "mahlif.sibelius.automation.detect_modal",
                                return_value=ModalType.EDIT_PLUGINS,
                            ):
                                with patch(
                                    "mahlif.sibelius.automation.get_front_window",
                                    return_value="Edit Plugins",
                                ):
                                    with patch(
                                        "mahlif.sibelius.automation.click_button",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "mahlif.sibelius.automation.dismiss_edit_plugins"
                                        ):
                                            result = reload_plugin("Test Plugin")
                                            assert result is True

    captured = capsys.readouterr()
    assert "Reloading plugin: Test Plugin" in captured.out
    assert "Plugin reloaded" in captured.out


def test_reload_plugin_dialog_not_open(capsys: pytest.CaptureFixture[str]) -> None:
    """Test reload_plugin when dialog doesn't open."""
    from mahlif.sibelius.automation import ModalType, reload_plugin

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.open_command_search"):
                with patch("mahlif.sibelius.automation.type_text"):
                    with patch("mahlif.sibelius.automation.press_key"):
                        with patch("mahlif.sibelius.automation.run_applescript"):
                            with patch(
                                "mahlif.sibelius.automation.detect_modal",
                                return_value=ModalType.NONE,
                            ):
                                with patch(
                                    "mahlif.sibelius.automation.get_front_window",
                                    return_value="untitled",
                                ):
                                    result = reload_plugin("Test")
                                    assert result is False

    captured = capsys.readouterr()
    assert "Failed to open Edit Plugins" in captured.out


def test_reload_plugin_unload_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """Test reload_plugin when Unload fails."""
    from mahlif.sibelius.automation import ModalType, reload_plugin

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.open_command_search"):
                with patch("mahlif.sibelius.automation.type_text"):
                    with patch("mahlif.sibelius.automation.press_key"):
                        with patch("mahlif.sibelius.automation.run_applescript"):
                            with patch(
                                "mahlif.sibelius.automation.detect_modal",
                                return_value=ModalType.EDIT_PLUGINS,
                            ):
                                with patch(
                                    "mahlif.sibelius.automation.click_button",
                                    return_value=False,
                                ):
                                    with patch(
                                        "mahlif.sibelius.automation.dismiss_edit_plugins"
                                    ):
                                        result = reload_plugin("Test")
                                        assert result is False

    captured = capsys.readouterr()
    assert "Failed to click Unload" in captured.out


def test_reload_plugin_reload_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """Test reload_plugin when Reload fails."""
    from mahlif.sibelius.automation import ModalType, reload_plugin

    click_calls = [0]

    def mock_click(name: str) -> bool:
        click_calls[0] += 1
        return click_calls[0] == 1

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.open_command_search"):
                with patch("mahlif.sibelius.automation.type_text"):
                    with patch("mahlif.sibelius.automation.press_key"):
                        with patch("mahlif.sibelius.automation.run_applescript"):
                            with patch(
                                "mahlif.sibelius.automation.detect_modal",
                                return_value=ModalType.EDIT_PLUGINS,
                            ):
                                with patch(
                                    "mahlif.sibelius.automation.click_button",
                                    side_effect=mock_click,
                                ):
                                    with patch(
                                        "mahlif.sibelius.automation.dismiss_edit_plugins"
                                    ):
                                        result = reload_plugin("Test")
                                        assert result is False

    captured = capsys.readouterr()
    assert "Failed to click Reload" in captured.out


def test_run_plugin(capsys: pytest.CaptureFixture[str]) -> None:
    """Test run_plugin via command search."""
    from mahlif.sibelius.automation import run_plugin

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.run_command"):
                with patch("mahlif.sibelius.automation.run_applescript"):
                    run_plugin("Test Plugin")

    captured = capsys.readouterr()
    assert "Running plugin: Test Plugin" in captured.out


def test_run_plugin_with_arrow_down() -> None:
    """Test run_plugin with arrow_down option."""
    from mahlif.sibelius.automation import run_plugin

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.run_command") as mock:
                with patch("mahlif.sibelius.automation.run_applescript"):
                    run_plugin("Test", arrow_down=1)
                    mock.assert_called_with("Test", arrow_down=1)


# =============================================================================
# Navigation
# =============================================================================


def test_go_to_bar() -> None:
    """Test go_to_bar function."""
    from mahlif.sibelius.automation import go_to_bar

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        go_to_bar(42)
        assert "42" in mock.call_args[0][0]


def test_go_to_page(capsys: pytest.CaptureFixture[str]) -> None:
    """Test go_to_page function."""
    from mahlif.sibelius.automation import go_to_page

    with patch("mahlif.sibelius.automation.run_command"):
        with patch("mahlif.sibelius.automation.run_applescript"):
            with patch("mahlif.sibelius.automation.type_text"):
                with patch("mahlif.sibelius.automation.press_key"):
                    go_to_page(5)

    captured = capsys.readouterr()
    assert "page 5" in captured.out


def test_scroll_to_start() -> None:
    """Test scroll_to_start function."""
    from mahlif.sibelius.automation import scroll_to_start

    with patch("mahlif.sibelius.automation.press_key") as mock:
        with patch("mahlif.sibelius.automation.run_applescript"):
            scroll_to_start()
            mock.assert_called_with("home", ["command"])


# =============================================================================
# Window Management
# =============================================================================


def test_list_windows() -> None:
    """Test list_windows returns get_windows result."""
    from mahlif.sibelius.automation import list_windows

    with patch("mahlif.sibelius.automation.get_windows", return_value=["win1", "win2"]):
        result = list_windows()
        assert result == ["win1", "win2"]


def test_switch_to_window_found() -> None:
    """Test switch_to_window when found."""
    from mahlif.sibelius.automation import switch_to_window

    with patch("mahlif.sibelius.automation.run_applescript", return_value="true"):
        result = switch_to_window("test")
        assert result is True


def test_switch_to_window_not_found() -> None:
    """Test switch_to_window when not found."""
    from mahlif.sibelius.automation import switch_to_window

    with patch("mahlif.sibelius.automation.run_applescript", return_value="false"):
        result = switch_to_window("test")
        assert result is False


# =============================================================================
# Utilities
# =============================================================================


def test_screenshot() -> None:
    """Test screenshot function."""
    from mahlif.sibelius.automation import screenshot

    with patch("mahlif.sibelius.automation.run_applescript"):
        result = screenshot("/tmp/test.png")
        assert result == Path("/tmp/test.png")


def test_notify() -> None:
    """Test notify function."""
    from mahlif.sibelius.automation import notify

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        notify("test message")
        assert "display notification" in mock.call_args[0][0]


def test_say() -> None:
    """Test say function."""
    from mahlif.sibelius.automation import say

    with patch("mahlif.sibelius.automation.run_applescript") as mock:
        say("hello")
        assert "say" in mock.call_args[0][0]


def test_starting(capsys: pytest.CaptureFixture[str]) -> None:
    """Test starting function."""
    from mahlif.sibelius.automation import starting

    with patch("mahlif.sibelius.automation.run_applescript"):
        with patch("mahlif.sibelius.automation.notify"):
            with patch("mahlif.sibelius.automation.say"):
                starting("test task")

    captured = capsys.readouterr()
    assert "Starting: test task" in captured.out


def test_done(capsys: pytest.CaptureFixture[str]) -> None:
    """Test done function."""
    from mahlif.sibelius.automation import done

    with patch("mahlif.sibelius.automation.run_applescript"):
        with patch("mahlif.sibelius.automation.notify"):
            with patch("mahlif.sibelius.automation.say"):
                done()

    captured = capsys.readouterr()
    assert "Done" in captured.out


# =============================================================================
# Legacy Compatibility
# =============================================================================


def test_dismiss_modal_legacy() -> None:
    """Test legacy dismiss_modal function."""
    from mahlif.sibelius.automation import dismiss_modal

    with patch("mahlif.sibelius.automation.press_key") as mock:
        with patch("mahlif.sibelius.automation.run_applescript"):
            dismiss_modal(count=2)
            assert mock.call_count == 2


def test_close_without_saving_legacy() -> None:
    """Test legacy close_without_saving function."""
    from mahlif.sibelius.automation import close_without_saving

    with patch("mahlif.sibelius.automation.close_score") as mock:
        close_without_saving()
        mock.assert_called_with(save=False)


def test_new_blank_score_legacy() -> None:
    """Test legacy new_blank_score function."""
    from mahlif.sibelius.automation import new_blank_score

    with patch("mahlif.sibelius.automation.create_blank_score") as mock:
        new_blank_score()
        mock.assert_called_once()


def test_compare_windows() -> None:
    """Test compare_windows function."""
    from mahlif.sibelius.automation import compare_windows

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("mahlif.sibelius.automation.activate"):
            with patch("mahlif.sibelius.automation.switch_to_window"):
                with patch("mahlif.sibelius.automation.go_to_page"):
                    with patch(
                        "mahlif.sibelius.automation.screenshot",
                        side_effect=lambda p: Path(p),
                    ):
                        path1, path2 = compare_windows("win1", "win2", tmpdir, page=1)
                        assert "win1" in str(path1)
                        assert "win2" in str(path2)


# =============================================================================
# Additional branch coverage
# =============================================================================


def test_dismiss_current_modal_message_box() -> None:
    """Test dismiss_current_modal with message box."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    with patch(
        "mahlif.sibelius.automation.detect_modal", return_value=ModalType.MESSAGE_BOX
    ):
        with patch(
            "mahlif.sibelius.automation.dismiss_message_box", return_value=True
        ) as mock:
            result = dismiss_current_modal()
            assert result is True
            mock.assert_called_once()


def test_dismiss_current_modal_save_changes() -> None:
    """Test dismiss_current_modal with save changes."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    with patch(
        "mahlif.sibelius.automation.detect_modal", return_value=ModalType.SAVE_CHANGES
    ):
        with patch(
            "mahlif.sibelius.automation.dismiss_save_changes", return_value=True
        ) as mock:
            result = dismiss_current_modal()
            assert result is True
            mock.assert_called_once()


def test_dismiss_current_modal_quick_start() -> None:
    """Test dismiss_current_modal with Quick Start."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    with patch(
        "mahlif.sibelius.automation.detect_modal", return_value=ModalType.QUICK_START
    ):
        with patch(
            "mahlif.sibelius.automation.dismiss_quick_start", return_value=True
        ) as mock:
            result = dismiss_current_modal()
            assert result is True
            mock.assert_called_once()


def test_dismiss_current_modal_edit_plugins() -> None:
    """Test dismiss_current_modal with Edit Plugins."""
    from mahlif.sibelius.automation import ModalType, dismiss_current_modal

    with patch(
        "mahlif.sibelius.automation.detect_modal", return_value=ModalType.EDIT_PLUGINS
    ):
        with patch(
            "mahlif.sibelius.automation.dismiss_edit_plugins", return_value=True
        ) as mock:
            result = dismiss_current_modal()
            assert result is True
            mock.assert_called_once()


def test_click_button_in_group_failure() -> None:
    """Test click_button_in_group fails gracefully."""
    from mahlif.sibelius.automation import click_button_in_group

    with patch(
        "mahlif.sibelius.automation.run_applescript",
        side_effect=RuntimeError("not found"),
    ):
        result = click_button_in_group("NonExistent")
        assert result is False


def test_ensure_blank_score_no_score_open() -> None:
    """Test ensure_blank_score when no score open."""
    from mahlif.sibelius.automation import ensure_blank_score

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.is_score_open", return_value=False):
            with patch(
                "mahlif.sibelius.automation.create_blank_score", return_value=True
            ) as mock:
                result = ensure_blank_score()
                assert result is True
                mock.assert_called_once()


def test_reload_plugin_window_name_fallback(capsys: pytest.CaptureFixture[str]) -> None:
    """Test reload_plugin when modal detection fails but window name works."""
    from mahlif.sibelius.automation import ModalType, reload_plugin

    with patch("mahlif.sibelius.automation.dismiss_all_modals"):
        with patch("mahlif.sibelius.automation.close_command_search"):
            with patch("mahlif.sibelius.automation.open_command_search"):
                with patch("mahlif.sibelius.automation.type_text"):
                    with patch("mahlif.sibelius.automation.press_key"):
                        with patch("mahlif.sibelius.automation.run_applescript"):
                            with patch(
                                "mahlif.sibelius.automation.detect_modal",
                                return_value=ModalType.NONE,  # Not EDIT_PLUGINS
                            ):
                                with patch(
                                    "mahlif.sibelius.automation.get_front_window",
                                    return_value="Edit Plugins",  # But window name has it
                                ):
                                    with patch(
                                        "mahlif.sibelius.automation.click_button",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "mahlif.sibelius.automation.dismiss_edit_plugins"
                                        ):
                                            result = reload_plugin("Test")
                                            # Should proceed since window name matched
                                            assert result is True


def test_type_in_field() -> None:
    """Test type_in_field selects all then types (replacing selection)."""
    from mahlif.sibelius.automation import type_in_field

    with patch("mahlif.sibelius.automation.press_key") as mock_press:
        with patch("mahlif.sibelius.automation.type_text") as mock_type:
            with patch("mahlif.sibelius.automation.run_applescript"):
                type_in_field("test")
                # Should select all with Cmd+A, then type (typing replaces selection)
                calls = [c[0][0] for c in mock_press.call_args_list]
                assert "a" in calls
                mock_type.assert_called_with("test", 0.1)
