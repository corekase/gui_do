"""Tests for TextInputControl (Feature 1)."""
import unittest
from unittest.mock import MagicMock, patch

import pygame
from pygame import Rect

from gui_do.core.gui_event import EventType, GuiEvent
from gui_do.controls.text_input_control import TextInputControl


def _make_app():
    app = MagicMock()
    app.focus = MagicMock()
    return app


def _make_ctrl(value="", **kwargs) -> TextInputControl:
    ctrl = TextInputControl("inp", Rect(10, 10, 200, 30), value=value, **kwargs)
    ctrl._focused = True
    return ctrl


def _key_event(key: int, mod: int = 0) -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_DOWN, type=0, key=key, mod=mod)


def _text_event(text: str) -> GuiEvent:
    return GuiEvent(kind=EventType.TEXT_INPUT, type=0, text=text)


def _mouse_down(x: int, y: int = 25) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(x, y), button=1)


def _mouse_up(x: int, y: int = 25) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=(x, y), button=1)


def _mouse_motion(x: int, y: int = 25) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=(x, y))


class TestTextInsertionViaTextInput(unittest.TestCase):
    def test_text_insertion_via_text_input_event(self) -> None:
        ctrl = _make_ctrl()
        changes = []
        ctrl._on_change = lambda v: changes.append(v)
        ctrl.handle_event(_text_event("hello"), _make_app())
        self.assertEqual(ctrl.value, "hello")
        self.assertEqual(changes, ["hello"])


class TestBackspaceDeletesBeforeCursor(unittest.TestCase):
    def test_backspace_deletes_before_cursor(self) -> None:
        ctrl = _make_ctrl(value="abc")
        ctrl.handle_event(_key_event(pygame.K_BACKSPACE), _make_app())
        self.assertEqual(ctrl.value, "ab")


class TestDeleteRemovesAfterCursor(unittest.TestCase):
    def test_delete_removes_after_cursor(self) -> None:
        ctrl = _make_ctrl(value="abc")
        ctrl._cursor_pos = 1
        ctrl.handle_event(_key_event(pygame.K_DELETE), _make_app())
        self.assertEqual(ctrl.value, "ac")


class TestLeftRightMovesCursor(unittest.TestCase):
    def test_left_right_moves_cursor(self) -> None:
        ctrl = _make_ctrl(value="hello")
        # cursor starts at 5
        ctrl.handle_event(_key_event(pygame.K_LEFT), _make_app())
        self.assertEqual(ctrl.cursor_pos, 4)
        ctrl.handle_event(_key_event(pygame.K_RIGHT), _make_app())
        self.assertEqual(ctrl.cursor_pos, 5)
        # clamped at 0
        for _ in range(10):
            ctrl.handle_event(_key_event(pygame.K_LEFT), _make_app())
        self.assertEqual(ctrl.cursor_pos, 0)


class TestHomeEndJumpsCursor(unittest.TestCase):
    def test_home_end_jumps_cursor(self) -> None:
        ctrl = _make_ctrl(value="hello")
        ctrl.handle_event(_key_event(pygame.K_HOME), _make_app())
        self.assertEqual(ctrl.cursor_pos, 0)
        ctrl.handle_event(_key_event(pygame.K_END), _make_app())
        self.assertEqual(ctrl.cursor_pos, 5)


class TestShiftArrowsExtendSelection(unittest.TestCase):
    def test_shift_arrows_extend_selection(self) -> None:
        ctrl = _make_ctrl(value="hello")
        ctrl._cursor_pos = 2
        ctrl.handle_event(_key_event(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT), _make_app())
        start, end = ctrl.selection_range
        self.assertEqual(start, 2)
        self.assertEqual(end, 3)


class TestCtrlASelectsAll(unittest.TestCase):
    def test_ctrl_a_selects_all(self) -> None:
        ctrl = _make_ctrl(value="hello")
        ctrl.handle_event(_key_event(pygame.K_a, mod=pygame.KMOD_CTRL), _make_app())
        self.assertEqual(ctrl.selection_range, (0, 5))


class TestBackspaceWithSelection(unittest.TestCase):
    def test_backspace_with_selection_deletes_selection(self) -> None:
        ctrl = _make_ctrl(value="hello")
        ctrl._sel_anchor = 1
        ctrl._sel_active = 4
        ctrl.handle_event(_key_event(pygame.K_BACKSPACE), _make_app())
        self.assertEqual(ctrl.value, "ho")


class TestInsertWithSelectionReplaces(unittest.TestCase):
    def test_insert_with_selection_replaces_selection(self) -> None:
        ctrl = _make_ctrl(value="hello")
        ctrl._sel_anchor = 0
        ctrl._sel_active = 5
        ctrl.handle_event(_text_event("X"), _make_app())
        self.assertEqual(ctrl.value, "X")


class TestOnSubmitFiresOnEnter(unittest.TestCase):
    def test_on_submit_fires_on_enter(self) -> None:
        submits = []
        ctrl = _make_ctrl(value="test", on_submit=lambda v: submits.append(v))
        ctrl.handle_event(_key_event(pygame.K_RETURN), _make_app())
        self.assertEqual(submits, ["test"])


class TestOnChangeNotFiredForSetValue(unittest.TestCase):
    def test_on_change_not_fired_for_programmatic_set_value(self) -> None:
        changes = []
        ctrl = _make_ctrl(on_change=lambda v: changes.append(v))
        ctrl.set_value("new_value")
        self.assertEqual(changes, [])
        self.assertEqual(ctrl.value, "new_value")


class TestMaskedModeRendersAsterisks(unittest.TestCase):
    def test_masked_mode_renders_asterisks(self) -> None:
        ctrl = _make_ctrl(value="secret", masked=True)
        self.assertEqual(ctrl._get_display_value(), "******")


class TestMaxLengthEnforced(unittest.TestCase):
    def test_max_length_enforced(self) -> None:
        ctrl = _make_ctrl(max_length=3)
        ctrl.handle_event(_text_event("hello"), _make_app())
        self.assertEqual(len(ctrl.value), 3)
        self.assertEqual(ctrl.value, "hel")


class TestDisabledGuard(unittest.TestCase):
    def test_disabled_guard(self) -> None:
        ctrl = _make_ctrl(value="abc")
        ctrl.enabled = False
        result = ctrl.handle_event(_text_event("X"), _make_app())
        self.assertFalse(result)
        self.assertEqual(ctrl.value, "abc")


class TestHiddenGuard(unittest.TestCase):
    def test_hidden_guard(self) -> None:
        ctrl = _make_ctrl(value="abc")
        ctrl.visible = False
        result = ctrl.handle_event(_text_event("X"), _make_app())
        self.assertFalse(result)
        self.assertEqual(ctrl.value, "abc")


class TestFocusGainedStartsTextInput(unittest.TestCase):
    def test_focus_gained_starts_text_input(self) -> None:
        ctrl = TextInputControl("inp", Rect(0, 0, 100, 30))
        with patch("pygame.key.start_text_input") as mock_start:
            ctrl._set_focused(True)
            mock_start.assert_called_once()


class TestFocusLostStopsTextInput(unittest.TestCase):
    def test_focus_lost_stops_text_input(self) -> None:
        ctrl = TextInputControl("inp", Rect(0, 0, 100, 30))
        ctrl._focused = True
        with patch("pygame.key.stop_text_input") as mock_stop:
            ctrl._set_focused(False)
            mock_stop.assert_called_once()


class TestCursorBlinkDrivesInvalidate(unittest.TestCase):
    def test_cursor_blink_drives_invalidate(self) -> None:
        ctrl = _make_ctrl()
        ctrl._focused = True
        ctrl._dirty = False
        # Force blink to trigger on next update by presetting elapsed past threshold
        ctrl._cursor_blink_elapsed = 0.4
        ctrl.update(0.15)  # total = 0.55 >= 0.5
        self.assertTrue(ctrl._dirty)


class TestScrollFollowsCursor(unittest.TestCase):
    def test_scroll_follows_cursor(self) -> None:
        ctrl = TextInputControl("inp", Rect(0, 0, 50, 30), value="a" * 50)
        ctrl._focused = True
        ctrl._cursor_pos = 50
        # Inject a mock font that returns non-zero widths so scroll can advance
        mock_font = MagicMock()
        mock_font.size = lambda text: (len(text) * 8, 16)  # 8px per char
        ctrl._get_font = lambda: mock_font
        ctrl._scroll_to_cursor()
        # Cursor is at the end; scroll should be > 0 since text is wider than control
        self.assertGreater(ctrl._scroll_offset_px, 0)


class TestAcceptsFocusRespectsTabIndex(unittest.TestCase):
    def test_accepts_focus_respects_tab_index(self) -> None:
        ctrl = TextInputControl("inp", Rect(0, 0, 100, 30))
        ctrl.tab_index = 0
        self.assertTrue(ctrl.accepts_focus())
        ctrl.tab_index = -1
        self.assertFalse(ctrl.accepts_focus())


if __name__ == "__main__":
    unittest.main()
