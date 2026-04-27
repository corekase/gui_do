"""Tests for ContextMenuManager."""
import unittest
from unittest.mock import MagicMock, patch

import pygame
from pygame import Rect

from gui_do.core.context_menu_manager import (
    ContextMenuManager,
    ContextMenuItem,
    ContextMenuHandle,
)


def _app_mock():
    app = MagicMock()
    app.surface.get_rect.return_value = Rect(0, 0, 1024, 768)
    # Simulate overlay.show returning an OverlayHandle-like object
    app.overlay.show.return_value = MagicMock()
    app.overlay.hide.return_value = True
    app.overlay.has_overlay.return_value = False
    return app


def _items():
    return [
        ContextMenuItem(label="Cut", action=MagicMock()),
        ContextMenuItem(label="Copy", action=MagicMock()),
        ContextMenuItem(label="", separator=True),
        ContextMenuItem(label="Paste", action=MagicMock()),
        ContextMenuItem(label="Delete", action=None, enabled=False),
    ]


class TestContextMenuItemDataclass(unittest.TestCase):
    def test_defaults(self) -> None:
        item = ContextMenuItem(label="X")
        self.assertEqual(item.label, "X")
        self.assertIsNone(item.action)
        self.assertTrue(item.enabled)
        self.assertFalse(item.separator)

    def test_separator_flag(self) -> None:
        item = ContextMenuItem(label="", separator=True)
        self.assertTrue(item.separator)

    def test_disabled_item(self) -> None:
        item = ContextMenuItem(label="Y", enabled=False)
        self.assertFalse(item.enabled)


class TestContextMenuManagerShow(unittest.TestCase):
    def test_show_returns_handle(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        handle = cm.show((100, 100), _items())
        self.assertIsInstance(handle, ContextMenuHandle)

    def test_show_calls_overlay_show(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        cm.show((100, 100), _items())
        app.overlay.show.assert_called_once()

    def test_handle_menu_id_registered(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        handle = cm.show((100, 100), _items())
        self.assertIn(handle.menu_id, cm._open_ids)

    def test_two_menus_get_unique_ids(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        h1 = cm.show((10, 10), _items())
        h2 = cm.show((20, 20), _items())
        self.assertNotEqual(h1.menu_id, h2.menu_id)


class TestContextMenuManagerDismiss(unittest.TestCase):
    def test_dismiss_by_id(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        handle = cm.show((100, 100), _items())
        result = cm.dismiss(handle.menu_id)
        self.assertTrue(result)

    def test_dismiss_nonexistent_returns_false(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        result = cm.dismiss("__nonexistent__")
        self.assertFalse(result)

    def test_dismiss_all(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        cm.show((10, 10), _items())
        cm.show((20, 20), _items())
        count = cm.dismiss_all()
        self.assertEqual(count, 2)

    def test_has_menu_false_after_dismiss(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        handle = cm.show((100, 100), _items())
        cm._dismiss_id(handle.menu_id)
        self.assertFalse(cm.has_menu(handle.menu_id))


class TestContextMenuManagerOnDismissCallback(unittest.TestCase):
    def test_on_dismiss_called_when_overlay_hides(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        dismissed = []
        handle = cm.show((100, 100), _items(), on_dismiss=lambda: dismissed.append(True))
        # Simulate the internal close path
        cm._dismiss_id(handle.menu_id)
        # The on_dismiss is registered with overlay.show; it fires when overlay.hide is called
        # We trigger it manually as would happen in production
        call_args = app.overlay.show.call_args
        on_dismiss_kwarg = call_args[1].get("on_dismiss") or call_args.kwargs.get("on_dismiss")
        if on_dismiss_kwarg:
            on_dismiss_kwarg()
        self.assertEqual(dismissed, [True])


class TestContextMenuPanelHandleEvent(unittest.TestCase):
    """Tests for _ContextMenuPanel event handling (unit-level)."""

    def _panel(self, items=None):
        from gui_do.core.context_menu_manager import _ContextMenuPanel
        if items is None:
            items = _items()
        closed = []
        panel = _ContextMenuPanel(
            "menu_1",
            Rect(100, 100, 150, 200),
            items,
            on_close=lambda: closed.append(True),
        )
        return panel, closed

    def _evt(self, kind, **kwargs):
        evt = MagicMock()
        evt.kind = kind
        for k, v in kwargs.items():
            setattr(evt, k, v)
        return evt

    def test_mouse_motion_sets_hovered_index(self) -> None:
        from gui_do.core.gui_event import EventType
        panel, _ = self._panel()
        rects = panel._item_rects()
        center = rects[0].center
        evt = self._evt(EventType.MOUSE_MOTION, pos=center)
        panel.handle_event(evt, MagicMock())
        self.assertEqual(panel._hovered_index, 0)

    def test_mouse_click_triggers_action(self) -> None:
        from gui_do.core.gui_event import EventType
        action = MagicMock()
        items = [ContextMenuItem(label="Do", action=action)]
        panel, closed = self._panel(items)
        rects = panel._item_rects()
        pos = (rects[0].x + 5, rects[0].y + 5)
        evt = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=pos)
        panel.handle_event(evt, MagicMock())
        action.assert_called_once()

    def test_mouse_click_disabled_item_not_activated(self) -> None:
        from gui_do.core.gui_event import EventType
        action = MagicMock()
        items = [ContextMenuItem(label="No", action=action, enabled=False)]
        panel, _ = self._panel(items)
        rects = panel._item_rects()
        pos = (rects[0].x + 5, rects[0].y + 5)
        evt = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=pos)
        panel.handle_event(evt, MagicMock())
        action.assert_not_called()

    def test_keyboard_down_advances_selection(self) -> None:
        from gui_do.core.gui_event import EventType
        items = [
            ContextMenuItem(label="A", action=MagicMock()),
            ContextMenuItem(label="B", action=MagicMock()),
        ]
        panel, _ = self._panel(items)
        panel._keyboard_index = 0
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_DOWN)
        panel.handle_event(evt, MagicMock())
        self.assertEqual(panel._keyboard_index, 1)

    def test_keyboard_up_decrements_selection(self) -> None:
        from gui_do.core.gui_event import EventType
        items = [
            ContextMenuItem(label="A", action=MagicMock()),
            ContextMenuItem(label="B", action=MagicMock()),
        ]
        panel, _ = self._panel(items)
        panel._keyboard_index = 1
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_UP)
        panel.handle_event(evt, MagicMock())
        self.assertEqual(panel._keyboard_index, 0)

    def test_keyboard_enter_activates_item(self) -> None:
        from gui_do.core.gui_event import EventType
        action = MagicMock()
        items = [ContextMenuItem(label="Go", action=action)]
        panel, _ = self._panel(items)
        panel._keyboard_index = 0
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_RETURN)
        panel.handle_event(evt, MagicMock())
        action.assert_called_once()

    def test_separator_skipped_in_keyboard_nav(self) -> None:
        from gui_do.core.gui_event import EventType
        items = [
            ContextMenuItem(label="A", action=MagicMock()),
            ContextMenuItem(label="", separator=True),
            ContextMenuItem(label="B", action=MagicMock()),
        ]
        panel, _ = self._panel(items)
        panel._keyboard_index = 0
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_DOWN)
        panel.handle_event(evt, MagicMock())
        # Should skip index 1 (separator) → land on index 2
        self.assertEqual(panel._keyboard_index, 2)


class TestContextMenuHandleIsOpen(unittest.TestCase):
    def test_handle_is_open_reflects_manager(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        handle = cm.show((10, 10), _items())
        # is_open checks cm.has_menu, which checks _open_ids
        self.assertTrue(cm.has_menu(handle.menu_id))

    def test_handle_dismiss(self) -> None:
        app = _app_mock()
        cm = ContextMenuManager(app)
        handle = cm.show((10, 10), _items())
        handle.dismiss()
        app.overlay.hide.assert_called()


if __name__ == "__main__":
    unittest.main()
