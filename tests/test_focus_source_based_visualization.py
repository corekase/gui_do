"""Tests for focus visualization based on event source (keyboard vs mouse)."""
import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect, Surface

from gui.app.gui_application import GuiApplication
from gui.controls.button_control import ButtonControl
from gui.controls.label_control import LabelControl
from gui.controls.panel_control import PanelControl
from gui.controls.window_control import WindowControl
from gui.core.focus_manager import FocusManager
from gui.core.focus_visualizer import FocusVisualizer
from gui.core.gui_event import GuiEvent, EventType
from gui.core.ui_node import UiNode


class FocusVisualizerSourceTests(unittest.TestCase):
    """Test set_focus_hint with show_hint parameter."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)

    def test_set_focus_hint_shows_hint_by_default(self) -> None:
        """Default behavior shows the hint."""
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.assertIs(self.visualizer._current_hint_node, node)
        self.assertEqual(self.visualizer._current_hint_elapsed, 0.0)

    def test_set_focus_hint_with_show_hint_true(self) -> None:
        """Explicitly showing hint stores the node."""
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node, show_hint=True)
        self.assertIs(self.visualizer._current_hint_node, node)

    def test_set_focus_hint_with_show_hint_false(self) -> None:
        """When show_hint=False, node is not stored for display."""
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node, show_hint=False)
        self.assertIsNone(self.visualizer._current_hint_node)

    def test_set_focus_hint_switching_with_show_hint_false(self) -> None:
        """Switching focus with show_hint=False clears any previous hint."""
        node1 = UiNode("n1", Rect(0, 0, 100, 100))
        node2 = UiNode("n2", Rect(100, 0, 100, 100))

        # First focus shows hint
        self.visualizer.set_focus_hint(node1, show_hint=True)
        self.assertIs(self.visualizer._current_hint_node, node1)

        # Second focus with show_hint=False clears it
        self.visualizer.set_focus_hint(node2, show_hint=False)
        self.assertIsNone(self.visualizer._current_hint_node)

    def test_set_focus_hint_switching_between_show_and_hide(self) -> None:
        """Can switch between showing and hiding the hint."""
        node1 = UiNode("n1", Rect(0, 0, 100, 100))
        node2 = UiNode("n2", Rect(100, 0, 100, 100))
        node3 = UiNode("n3", Rect(200, 0, 100, 100))

        # Show node1
        self.visualizer.set_focus_hint(node1, show_hint=True)
        self.assertIs(self.visualizer._current_hint_node, node1)

        # Hide node2
        self.visualizer.set_focus_hint(node2, show_hint=False)
        self.assertIsNone(self.visualizer._current_hint_node)

        # Show node3
        self.visualizer.set_focus_hint(node3, show_hint=True)
        self.assertIs(self.visualizer._current_hint_node, node3)


class FocusManagerSourceTests(unittest.TestCase):
    """Test FocusManager passes show_hint parameter correctly."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)
        self.manager = FocusManager(visualizer=self.visualizer)

    def test_set_focus_shows_hint_by_default(self) -> None:
        """Default set_focus shows the hint."""
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.manager.set_focus(node)
        self.assertIs(self.visualizer._current_hint_node, node)

    def test_set_focus_with_show_hint_false(self) -> None:
        """set_focus with show_hint=False doesn't show hint."""
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.manager.set_focus(node, show_hint=False)
        self.assertIsNone(self.visualizer._current_hint_node)

    def test_set_focus_with_show_hint_true(self) -> None:
        """set_focus with show_hint=True shows hint."""
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.manager.set_focus(node, show_hint=True)
        self.assertIs(self.visualizer._current_hint_node, node)

    def test_cycle_focus_shows_hint(self) -> None:
        """cycle_focus (keyboard Tab) shows hint by default."""
        from gui.core.scene import Scene

        n1 = UiNode("n1", Rect(0, 0, 100, 100))
        n1.set_tab_index(0)
        n2 = UiNode("n2", Rect(100, 0, 100, 100))
        n2.set_tab_index(1)

        scene = Scene()
        scene.add(n1)
        scene.add(n2)

        self.manager.cycle_focus(scene, forward=True)
        # First cycle should show hint
        self.assertIs(self.visualizer._current_hint_node, n1)


class MouseClickFocusIntegrationTests(unittest.TestCase):
    """Integration test: mouse clicks don't show focus hint."""

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

    def test_mouse_click_does_not_show_focus_hint(self) -> None:
        """Clicking a button focuses it but doesn't show the focus hint."""
        # Initially no hint
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)

        # Click on button1
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (100, 70), "button": 1},
            )
        )

        # Button1 is focused
        self.assertIs(self.app.focus.focused_node, self.button1)
        # But hint is not shown (because it was a mouse click)
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)

    def test_keyboard_focus_shows_hint(self) -> None:
        """Tab key focuses a button and shows the focus hint."""
        # Initially no hint
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)

        # Focus button1 via tab
        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB},
            )
        )

        # Button1 should be focused and hint should be shown
        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertIs(self.app.focus_visualizer._current_hint_node, self.button1)

    def test_switch_from_keyboard_to_mouse_clears_hint(self) -> None:
        """After focusing with Tab, clicking another button clears the hint."""
        # Focus button1 via tab (shows hint)
        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB},
            )
        )
        self.assertIs(self.app.focus_visualizer._current_hint_node, self.button1)

        # Click button2 (should clear hint)
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (250, 70), "button": 1},
            )
        )

        # Button2 is focused but hint is cleared
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)

    def test_switch_from_mouse_to_keyboard_shows_hint(self) -> None:
        """After mouse focus with no hint, first Tab shows hint on current focus."""
        # Click button1 (no hint)
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": (100, 70), "button": 1},
            )
        )
        self.assertIsNone(self.app.focus_visualizer._current_hint_node)

        # First Tab shows the hint on the current focus target (no advance yet)
        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB},
            )
        )

        self.assertIs(self.app.focus.focused_node, self.button1)
        self.assertIs(self.app.focus_visualizer._current_hint_node, self.button1)

        # While hint is active, next Tab advances focus and resets hint to the new target.
        self.app.process_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_TAB},
            )
        )
        self.assertIs(self.app.focus.focused_node, self.button2)
        self.assertIs(self.app.focus_visualizer._current_hint_node, self.button2)

    def test_clicking_label_does_not_clear_existing_focus(self) -> None:
        """Mouse clicking labels must not change active focus."""
        label = self.window.add(LabelControl("lbl", Rect(40, 130, 180, 40), "Info"))
        label.set_tab_index(2)  # Even if explicitly focusable, labels must ignore mouse focus.

        self.app.focus.set_focus(self.button1, show_hint=False)
        self.assertIs(self.app.focus.focused_node, self.button1)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": label.rect.center, "button": 1},
            )
        )

        self.assertIs(self.app.focus.focused_node, self.button1)

    def test_clicking_label_with_no_focus_keeps_focus_none(self) -> None:
        """Clicking labels with no existing focus should not establish focus."""
        label = self.window.add(LabelControl("lbl", Rect(40, 130, 180, 40), "Info"))
        label.set_tab_index(2)

        self.assertIsNone(self.app.focus.focused_node)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": label.rect.center, "button": 1},
            )
        )

        self.assertIsNone(self.app.focus.focused_node)


if __name__ == "__main__":
    unittest.main()
