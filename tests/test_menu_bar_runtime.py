"""Tests for MenuBarControl and MenuBarManager."""
import sys
import types
import unittest
from unittest.mock import MagicMock
from pygame import Rect

# Provide a minimal pygame stub if pygame is not available under display
import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from gui_do.controls.menu_bar_control import MenuBarControl, MenuEntry
from gui_do.core.menu_bar_manager import MenuBarManager
from gui_do.core.context_menu_manager import ContextMenuItem


def _make_app() -> MagicMock:
    app = MagicMock()
    app.surface.get_rect.return_value = Rect(0, 0, 800, 600)
    app.overlay.has_overlay.return_value = False
    return app


class TestMenuBarManagerRegistration(unittest.TestCase):

    def test_register_single_menu(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [ContextMenuItem("Open")])
        self.assertEqual(mgr.menu_labels, ["File"])

    def test_register_extends_existing_menu(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [ContextMenuItem("Open")])
        mgr.register_menu("File", [ContextMenuItem("Save")])
        items = mgr.items_for("File")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].label, "Open")
        self.assertEqual(items[1].label, "Save")

    def test_register_preserves_order(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [])
        mgr.register_menu("Edit", [])
        mgr.register_menu("View", [])
        self.assertEqual(mgr.menu_labels, ["File", "Edit", "View"])

    def test_build_returns_menu_bar_control(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [ContextMenuItem("Quit")])
        bar = mgr.build("bar", Rect(0, 0, 800, 28))
        self.assertIsInstance(bar, MenuBarControl)
        self.assertEqual(len(bar.entries), 1)
        self.assertEqual(bar.entries[0].label, "File")

    def test_set_enabled_disables_menu(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [ContextMenuItem("Open")])
        mgr.set_enabled("File", False)
        bar = mgr.build("bar", Rect(0, 0, 800, 28))
        self.assertFalse(bar.entries[0].enabled)

    def test_clear_removes_all(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [])
        mgr.clear()
        self.assertEqual(mgr.menu_labels, [])

    def test_items_for_unknown_returns_empty(self):
        mgr = MenuBarManager()
        self.assertEqual(mgr.items_for("Unknown"), [])


class TestMenuBarControlBasics(unittest.TestCase):

    def _make_bar(self):
        entries = [
            MenuEntry("File", [ContextMenuItem("Open"), ContextMenuItem("Quit")]),
            MenuEntry("Edit", [ContextMenuItem("Undo")]),
        ]
        return MenuBarControl("bar", Rect(0, 0, 800, 28), entries)

    def test_initial_state(self):
        bar = self._make_bar()
        self.assertEqual(len(bar.entries), 2)
        self.assertEqual(bar._open_index, -1)

    def test_set_entries_resets_state(self):
        bar = self._make_bar()
        bar._open_index = 0
        bar.set_entries([MenuEntry("Help", [])])
        self.assertEqual(len(bar.entries), 1)
        self.assertEqual(bar._open_index, -1)

    def test_disabled_bar_ignores_events(self):
        bar = self._make_bar()
        bar.enabled = False
        app = _make_app()
        from gui_do.core.gui_event import GuiEvent, EventType
        evt = MagicMock()
        evt.kind = EventType.MOUSE_BUTTON_DOWN
        evt.button = 1
        evt.pos = (10, 14)
        result = bar.handle_event(evt, app)
        self.assertFalse(result)

    def test_draw_does_not_raise(self):
        bar = self._make_bar()
        surface = pygame.Surface((800, 600))
        theme = MagicMock()
        theme.panel = (40, 40, 50)
        theme.text = (220, 220, 220)
        theme.highlight = (0, 100, 200)
        theme.accent = (0, 80, 160)
        theme.border = (60, 60, 70)
        bar.draw(surface, theme)  # should not raise


if __name__ == "__main__":
    unittest.main()
