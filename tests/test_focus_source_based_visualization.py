"""Tests for focus visualization -- hint is keyboard-driven, not mouse-driven."""
import unittest
from unittest.mock import patch

import pygame
from pygame import Rect, Surface

from gui.app.gui_application import GuiApplication
from gui.controls.button_control import ButtonControl
from gui.controls.label_control import LabelControl
from gui.controls.panel_control import PanelControl
from gui.controls.window_control import WindowControl
from gui.core.focus_manager import FocusManager
from gui.core.focus_visualizer import FocusVisualizer
from gui.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS
from gui.core.scene import Scene
from gui.core.ui_node import UiNode


class FocusVisualizerKeyboardHintTests(unittest.TestCase):
    """Hint visibility is keyboard-driven even when focus exists."""

    def _make(self):
        manager = FocusManager()
        app = type("App", (), {"focus": manager})()
        return FocusVisualizer(app), manager

    def test_cycle_focus_makes_hint_active(self) -> None:
        vis, mgr = self._make()
        n1 = UiNode("n1", Rect(0, 0, 100, 100))
        n1.set_tab_index(0)
        scene = Scene()
        scene.add(n1)
        mgr.cycle_focus(scene, forward=True)
        self.assertIs(mgr.focused_node, n1)
        self.assertTrue(vis.has_active_hint())

    def test_set_focus_from_non_keyboard_does_not_show_hint(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        self.assertFalse(vis.has_active_hint())

    def test_set_focus_via_keyboard_makes_hint_active(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)), via_keyboard=True)
        self.assertTrue(vis.has_active_hint())

    def test_clear_focus_deactivates_hint(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        mgr.clear_focus()
        self.assertFalse(vis.has_active_hint())


class MouseClickFocusIntegrationTests(unittest.TestCase):
    """Integration tests: mouse focus does not activate hint; keyboard does."""

    def setUp(self) -> None:
        pygame.init()
        self.surface = Surface((400, 300))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))
        self.window = self.root.add(WindowControl("main_win", Rect(20, 20, 360, 260), "Main"))
        self.window.active = True
        self.button1 = self.window.add(ButtonControl("btn1", Rect(50, 50, 100, 40), "Button 1"))
        self.button1.set_tab_index(0)
        self.button2 = self.window.add(ButtonControl("btn2", Rect(200, 50, 100, 40), "Button 2"))
        self.button2.set_tab_index(1)

    def tearDown(self) -> None:
        pygame.quit()

    def test_mouse_click_focuses_without_showing_hint(self) -> None:
        """Clicking a button focuses it but does not activate the keyboard hint."""
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))

        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

    def test_keyboard_tab_focuses_and_shows_hint(self) -> None:
        """Tab key focuses a button; hint is active."""
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))

        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_tab_after_mouse_click_first_shows_hint_then_advances(self) -> None:
        """After mouse focus, first Tab reveals hint; second Tab advances focus."""
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_tab_initiation_gate_expires_then_requires_hint_reinit(self) -> None:
        """If second Tab is late (after timeout), first-Tab hint gate is required again."""
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 70), "button": 1}))
        self.assertIs(self.app.focus.focused_node, self.button1)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS + 0.01)
        self.assertFalse(self.app.focus_visualizer.has_active_hint())

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

    def test_titlebar_click_does_not_focus_screen_control_under_window(self) -> None:
        """Mouse focus selection must not fall through top window titlebar to screen controls."""
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300)))
        under = root.add(ButtonControl("under", Rect(30, 30, 100, 20), "Under"))
        under.set_tab_index(0)
        win = root.add(WindowControl("overlay", Rect(20, 20, 260, 180), "Styles"))

        screen_events = []
        app.set_screen_lifecycle(event_handler=lambda _event: (screen_events.append("screen") or False))

        app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": win.title_bar_rect().center, "button": 1}))

        self.assertTrue(win.active)
        self.assertIsNone(app.focus.focused_node)
        self.assertEqual(screen_events, [])

    def test_clicking_label_does_not_clear_existing_focus(self) -> None:
        """Mouse clicking labels must not change active focus."""
        label = self.window.add(LabelControl("lbl", Rect(40, 130, 180, 40), "Info"))
        label.set_tab_index(2)

        self.app.focus.set_focus(self.button1)
        self.assertIs(self.app.focus.focused_node, self.button1)

        self.app.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": label.rect.center, "button": 1})
        )

        self.assertIs(self.app.focus.focused_node, self.button1)

    def test_clicking_label_with_no_focus_keeps_focus_none(self) -> None:
        """Clicking labels with no existing focus should not establish focus."""
        label = self.window.add(LabelControl("lbl", Rect(40, 130, 180, 40), "Info"))
        label.set_tab_index(2)

        self.assertIsNone(self.app.focus.focused_node)

        self.app.process_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": label.rect.center, "button": 1})
        )

        self.assertIsNone(self.app.focus.focused_node)

    def test_keyboard_focus_cycle_clears_hover_when_pointer_moved_off_without_motion_event(self) -> None:
        """Tab cycling must clear stale hover state using live pointer position."""
        self.app.process_event(
            pygame.event.Event(pygame.MOUSEMOTION, {"pos": self.button1.rect.center, "rel": (0, 0), "buttons": (0, 0, 0)})
        )
        self.assertTrue(self.button1.hovered)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(self.app.focus.focused_node, self.button1)

        off_pos = (self.window.rect.right + 20, self.window.rect.bottom + 20)
        with patch("pygame.mouse.get_pos", return_value=off_pos):
            self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))

        self.assertFalse(self.button1.hovered)
        self.assertIs(self.app.focus.focused_node, self.button2)

    def test_screen_hint_drawn_before_window_so_window_implicitly_occludes(self) -> None:
        """Screen focus hint should be emitted before windows, so windows can overdraw it."""
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300), draw_background=False))
        screen_btn = root.add(ButtonControl("screen_btn", Rect(40, 40, 120, 30), "Screen"))
        screen_btn.set_tab_index(0)
        win = root.add(WindowControl("styles", Rect(20, 20, 260, 180), "Styles"))

        # Seed screen-scope keyboard hint directly.
        app.focus.set_focus(screen_btn, via_keyboard=True)
        self.assertIs(app.focus.focused_node, screen_btn)
        self.assertTrue(app.focus_visualizer.has_active_hint())

        call_order = []
        def _record_button_draw(_button_self, _surface, _theme):
            call_order.append("screen")

        def _record_window_draw(_window_self, _surface, _theme):
            call_order.append("window")

        with patch.object(ButtonControl, "draw", new=_record_button_draw):
            with patch.object(WindowControl, "draw", new=_record_window_draw):
                original_screen_hint = app.focus_visualizer.draw_hint_for_scene_root

                def _record_screen_hint(*args, **kwargs):
                    call_order.append("hint")
                    return original_screen_hint(*args, **kwargs)

                with patch.object(app.focus_visualizer, "draw_hint_for_scene_root", side_effect=_record_screen_hint) as mock_screen_hint:
                    app.scene.draw(app.surface, app.theme, app=app)
                    self.assertGreaterEqual(mock_screen_hint.call_count, 1)

        self.assertIn("hint", call_order)
        self.assertIn("window", call_order)
        self.assertLess(call_order.index("hint"), call_order.index("window"))

    def test_window_focus_hint_draws_in_window_phase(self) -> None:
        """Window-scoped focus hint remains visible by drawing after its window draw."""
        app = GuiApplication(Surface((400, 300)))
        root = app.add(PanelControl("root", Rect(0, 0, 400, 300), draw_background=False))
        win = root.add(WindowControl("styles", Rect(20, 20, 260, 180), "Styles"))
        win.active = True
        win_btn = win.add(ButtonControl("win_btn", Rect(50, 60, 100, 30), "InWin"))
        win_btn.set_tab_index(0)

        # First Tab focuses first candidate in window scope and shows hint.
        app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_TAB}))
        self.assertIs(app.focus.focused_node, win_btn)
        self.assertTrue(app.focus_visualizer.has_active_hint())

        with patch.object(WindowControl, "draw", return_value=None):
            with patch.object(app.focus_visualizer, "draw_hint_for_window", wraps=app.focus_visualizer.draw_hint_for_window) as mock_window_hint:
                app.scene.draw(app.surface, app.theme, app=app)
                self.assertGreaterEqual(mock_window_hint.call_count, 1)


if __name__ == "__main__":
    unittest.main()
