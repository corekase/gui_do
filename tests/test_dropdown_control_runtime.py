"""Tests for DropdownControl (Feature 7)."""
import unittest
from unittest.mock import MagicMock, patch

import pygame
from pygame import Rect

from gui_do.controls.dropdown_control import DropdownControl, DropdownOption
from gui_do.core.gui_event import EventType, GuiEvent


def _opts(n=4):
    return [DropdownOption(label=f"Opt {i}", value=i) for i in range(n)]


def _ctrl(**kwargs) -> DropdownControl:
    return DropdownControl("dd", Rect(50, 50, 160, 30), _opts(), **kwargs)


def _app():
    app = MagicMock()
    app.overlay = MagicMock()
    app.overlay.anchor_position = MagicMock(return_value=(50, 80))
    app.overlay.show = MagicMock()
    app.overlay.hide = MagicMock()
    app.overlay.has_overlay = MagicMock(return_value=False)
    return app


def _click_on(ctrl: DropdownControl) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=ctrl.rect.center, button=1)


def _key(k: int) -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_DOWN, type=0, key=k, mod=0)


class TestClickOpensDropdown(unittest.TestCase):
    def test_click_opens_dropdown(self) -> None:
        ctrl = _ctrl()
        app = _app()
        ctrl.handle_event(_click_on(ctrl), app)
        self.assertTrue(ctrl.is_open)


class TestClickAgainClosesDropdown(unittest.TestCase):
    def test_click_again_closes_dropdown(self) -> None:
        ctrl = _ctrl()
        app = _app()
        ctrl._is_open = True
        ctrl.handle_event(_click_on(ctrl), app)
        self.assertFalse(ctrl.is_open)


class TestEnterKeyOpens(unittest.TestCase):
    def test_enter_key_opens_when_closed(self) -> None:
        ctrl = _ctrl()
        ctrl._focused = True
        app = _app()
        ctrl.handle_event(_key(pygame.K_RETURN), app)
        self.assertTrue(ctrl.is_open)


class TestEscapeKeyCloses(unittest.TestCase):
    def test_escape_closes_when_open(self) -> None:
        ctrl = _ctrl()
        ctrl._focused = True
        ctrl._is_open = True
        app = _app()
        ctrl.handle_event(_key(pygame.K_ESCAPE), app)
        self.assertFalse(ctrl.is_open)


class TestArrowDownChangesSelectionWhenClosed(unittest.TestCase):
    def test_arrow_down_changes_selection_when_closed(self) -> None:
        ctrl = _ctrl(selected_index=0)
        ctrl._focused = True
        changes = []
        ctrl._on_change = lambda v, i: changes.append(i)
        ctrl.handle_event(_key(pygame.K_DOWN), _app())
        self.assertEqual(ctrl.selected_index, 1)
        self.assertEqual(changes, [1])


class TestArrowUpChangesSelectionWhenClosed(unittest.TestCase):
    def test_arrow_up_changes_selection_when_closed(self) -> None:
        ctrl = _ctrl(selected_index=2)
        ctrl._focused = True
        changes = []
        ctrl._on_change = lambda v, i: changes.append(i)
        ctrl.handle_event(_key(pygame.K_UP), _app())
        self.assertEqual(ctrl.selected_index, 1)
        self.assertEqual(changes, [1])


class TestOnChangeNotFiredIfSameIndex(unittest.TestCase):
    def test_on_change_not_fired_if_already_at_boundary(self) -> None:
        ctrl = _ctrl(selected_index=0)
        ctrl._focused = True
        changes = []
        ctrl._on_change = lambda v, i: changes.append(i)
        ctrl.handle_event(_key(pygame.K_UP), _app())
        self.assertEqual(changes, [])


class TestSelectedOptionProperty(unittest.TestCase):
    def test_selected_option_returns_correct(self) -> None:
        ctrl = _ctrl(selected_index=2)
        self.assertEqual(ctrl.selected_option.value, 2)


class TestDefaultSelectionOnCreation(unittest.TestCase):
    def test_defaults_to_first_option_when_unspecified(self) -> None:
        ctrl = _ctrl()
        self.assertEqual(ctrl.selected_index, 0)


class TestSetOptionsResetSelection(unittest.TestCase):
    def test_set_options_resets_selection(self) -> None:
        ctrl = _ctrl(selected_index=1)
        ctrl.set_options([DropdownOption("X")])
        self.assertEqual(ctrl.selected_index, 0)


class TestGuardDisabled(unittest.TestCase):
    def test_guard_disabled_returns_false(self) -> None:
        ctrl = _ctrl()
        ctrl.enabled = False
        self.assertFalse(ctrl.handle_event(_click_on(ctrl), _app()))
        self.assertFalse(ctrl.is_open)


class TestGuardHidden(unittest.TestCase):
    def test_guard_hidden_returns_false(self) -> None:
        ctrl = _ctrl()
        ctrl.visible = False
        self.assertFalse(ctrl.handle_event(_click_on(ctrl), _app()))


class TestEmptyOptionsDoesNotOpenOverlay(unittest.TestCase):
    def test_empty_options_does_not_open(self) -> None:
        ctrl = DropdownControl("dd", Rect(50, 50, 160, 30), [])
        ctrl.handle_event(_click_on(ctrl), _app())
        self.assertFalse(ctrl.is_open)


class TestOnOverlayDismissSetsIsOpenFalse(unittest.TestCase):
    def test_on_overlay_dismiss_sets_is_open_false(self) -> None:
        ctrl = _ctrl()
        ctrl._is_open = True
        ctrl._on_overlay_dismiss()
        self.assertFalse(ctrl.is_open)


class TestAcceptsFocusRespectedTabIndex(unittest.TestCase):
    def test_accepts_focus_true_when_tab_index_zero(self) -> None:
        ctrl = _ctrl()
        self.assertTrue(ctrl.accepts_focus())
        ctrl.tab_index = -1
        self.assertFalse(ctrl.accepts_focus())


if __name__ == "__main__":
    unittest.main()
