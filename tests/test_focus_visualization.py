"""Tests for focus visualization -- hint is gated by keyboard focus activity."""
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.core.focus_visualizer import FocusVisualizer
from gui_do.core.focus_manager import FocusManager
from gui_do.core.ui_node import UiNode
from gui_do.core.scene import Scene
from gui_do.theme.color_theme import ColorTheme


class FocusVisualizerQueryTests(unittest.TestCase):
    """has_active_hint() reflects keyboard-driven hint eligibility."""

    def _make(self):
        manager = FocusManager()
        app = SimpleNamespace(focus=manager)
        return FocusVisualizer(app), manager

    def test_has_active_hint_false_when_nothing_focused(self) -> None:
        vis, _ = self._make()
        self.assertFalse(vis.has_active_hint())

    def test_has_active_hint_true_when_node_focused_via_keyboard(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)), via_keyboard=True)
        self.assertTrue(vis.has_active_hint())

    def test_has_active_hint_false_when_node_focused_via_mouse_or_programmatic(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        self.assertFalse(vis.has_active_hint())

    def test_has_active_hint_false_after_focus_cleared(self) -> None:
        vis, mgr = self._make()
        mgr.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        mgr.clear_focus()
        self.assertFalse(vis.has_active_hint())


class FocusVisualizerDrawingTests(unittest.TestCase):
    """Drawing behaviour -- hint drawn for focused node, nothing when unfocused."""

    def setUp(self) -> None:
        self.manager = FocusManager()
        self.app = SimpleNamespace(focus=self.manager)
        self.visualizer = FocusVisualizer(self.app)
        self.theme = ColorTheme()
        self.surface = pygame.Surface((800, 600))

    def test_draw_hints_no_crash_with_no_focus(self) -> None:
        self.visualizer.draw_hints(self.surface, self.theme)  # Must not raise

    def test_draw_hints_skips_invisible_nodes(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        node.visible = False
        self.manager.set_focus(node, via_keyboard=True)
        self.visualizer.draw_hints(self.surface, self.theme)  # Must not raise

    def test_draw_hints_skips_node_with_degenerate_rect(self) -> None:
        node = UiNode("n", Rect(0, 0, 1, 1))
        self.manager.set_focus(node, via_keyboard=True)
        with patch("pygame.draw.line") as mock_line:
            self.visualizer.draw_hints(self.surface, self.theme)
            mock_line.assert_not_called()

    def test_draw_hints_draws_when_node_focused(self) -> None:
        node = UiNode("n", Rect(10, 10, 100, 100))
        self.manager.set_focus(node, via_keyboard=True)
        with patch("pygame.draw.line") as mock_line:
            self.visualizer.draw_hints(self.surface, self.theme)
            self.assertGreater(mock_line.call_count, 0)

    def test_draw_hints_does_not_draw_for_non_keyboard_focus(self) -> None:
        node = UiNode("n", Rect(10, 10, 100, 100))
        self.manager.set_focus(node)
        with patch("pygame.draw.line") as mock_line:
            self.visualizer.draw_hints(self.surface, self.theme)
            mock_line.assert_not_called()

    def test_draw_hints_does_not_draw_when_nothing_focused(self) -> None:
        with patch("pygame.draw.line") as mock_line:
            self.visualizer.draw_hints(self.surface, self.theme)
            mock_line.assert_not_called()

    def test_draw_dashed_rect_draws_lines(self) -> None:
        rect = Rect(10, 10, 100, 100)
        with patch("pygame.draw.line") as mock_line:
            self.visualizer._draw_dashed_rectangle(self.surface, rect, (255, 0, 0))
            self.assertGreater(mock_line.call_count, 0)


class FocusManagerIntegrationTests(unittest.TestCase):
    """Visualizer tracks focus manager state correctly."""

    def setUp(self) -> None:
        self.manager = FocusManager()
        self.app = SimpleNamespace(focus=self.manager)
        self.visualizer = FocusVisualizer(self.app)

    def test_focus_manager_without_visualizer_no_crash(self) -> None:
        manager = FocusManager()
        manager.set_focus(UiNode("n", Rect(0, 0, 100, 100)))  # Must not raise

    def test_set_focus_makes_hint_active(self) -> None:
        self.manager.set_focus(UiNode("n", Rect(0, 0, 100, 100)), via_keyboard=True)
        self.assertTrue(self.visualizer.has_active_hint())

    def test_set_focus_without_keyboard_keeps_hint_inactive(self) -> None:
        self.manager.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        self.assertFalse(self.visualizer.has_active_hint())

    def test_clear_focus_makes_hint_inactive(self) -> None:
        self.manager.set_focus(UiNode("n", Rect(0, 0, 100, 100)))
        self.manager.clear_focus()
        self.assertFalse(self.visualizer.has_active_hint())

    def test_switch_focus_reflected_in_hint(self) -> None:
        n1 = UiNode("n1", Rect(0, 0, 100, 100))
        n2 = UiNode("n2", Rect(100, 0, 100, 100))
        self.manager.set_focus(n1, via_keyboard=True)
        self.manager.set_focus(n2, via_keyboard=True)
        self.assertIs(self.manager.focused_node, n2)
        self.assertTrue(self.visualizer.has_active_hint())


class FocusVisualizerEdgeCasesTests(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def test_tiny_control_not_drawn(self) -> None:
        manager = FocusManager()
        manager.set_focus(UiNode("n", Rect(0, 0, 1, 1)), via_keyboard=True)
        vis = FocusVisualizer(SimpleNamespace(focus=manager))
        vis.draw_hints(pygame.Surface((800, 600)), ColorTheme())  # Must not raise

    def test_multiple_focus_switches_latest_reflected(self) -> None:
        manager = FocusManager()
        vis = FocusVisualizer(SimpleNamespace(focus=manager))
        n1 = UiNode("n1", Rect(0, 0, 100, 100))
        n2 = UiNode("n2", Rect(100, 0, 100, 100))
        n3 = UiNode("n3", Rect(200, 0, 100, 100))
        manager.set_focus(n1, via_keyboard=True)
        manager.set_focus(n2, via_keyboard=True)
        manager.set_focus(n3, via_keyboard=True)
        self.assertIs(manager.focused_node, n3)
        self.assertTrue(vis.has_active_hint())


class SceneFocusHintOrderingTests(unittest.TestCase):
    """Regression tests for scene-ordered hint rendering."""

    def test_scene_draw_calls_hint_draw_after_each_visible_root(self) -> None:
        surface = pygame.Surface((320, 240))
        theme = ColorTheme()
        call_order = []

        class _RecordingNode(UiNode):
            def __init__(self, control_id: str, rect: Rect, marker: str) -> None:
                super().__init__(control_id, rect)
                self.marker = marker

            def draw(self, _surface, _theme) -> None:
                call_order.append(f"draw:{self.marker}")

        root_a = _RecordingNode("root_a", Rect(0, 0, 40, 40), "a")
        root_b = _RecordingNode("root_b", Rect(50, 0, 40, 40), "b")

        visualizer = MagicMock()
        visualizer.draw_hint_for_scene_root.side_effect = lambda *_args: call_order.append("hint")
        app = SimpleNamespace(focus_visualizer=visualizer)

        scene = Scene()
        scene.add(root_a)
        scene.add(root_b)
        scene.draw(surface, theme, app=app)

        self.assertEqual(call_order, ["draw:a", "hint", "draw:b", "hint"])

    def test_panel_root_draws_screen_hint_before_window_phase(self) -> None:
        surface = pygame.Surface((320, 240))
        theme = ColorTheme()
        call_order = []

        class _RecordingPanel(UiNode):
            def draw_screen_phase(self, _surface, _theme) -> None:
                call_order.append("screen")

            def draw_window_phase(self, _surface, _theme, app=None) -> None:
                del app
                call_order.append("windows")

            def draw(self, _surface, _theme) -> None:
                call_order.append("legacy")

        root = _RecordingPanel("root", Rect(0, 0, 40, 40))
        visualizer = MagicMock()
        visualizer.draw_hint_for_scene_root.side_effect = lambda *_args: call_order.append("hint")
        app = SimpleNamespace(focus_visualizer=visualizer)

        scene = Scene()
        scene.add(root)
        scene.draw(surface, theme, app=app)

        self.assertEqual(call_order, ["screen", "hint", "windows"])


class FocusHintWindowOcclusionTests(unittest.TestCase):
    """Hints draw unconditionally; painter's order handles window occlusion."""

    def test_hint_draws_fully_regardless_of_overlapping_window(self) -> None:
        """Hint renders all dashes even when a window rect covers the target.

        Occlusion is handled by draw order (windows drawn after screen hints),
        not by per-dash clipping inside the visualizer.
        """
        class _WindowStub(UiNode):
            def is_window(self) -> bool:
                return True

        manager = FocusManager()
        target = UiNode("target", Rect(40, 40, 20, 20))
        manager.set_focus(target, via_keyboard=True)

        window = _WindowStub("win", Rect(0, 0, 120, 120))
        scene = Scene()
        scene.add(target)
        scene.add(window)

        app = SimpleNamespace(focus=manager)
        visualizer = FocusVisualizer(app)

        surface = pygame.Surface((160, 120))
        theme = ColorTheme()
        with patch("pygame.draw.line") as mock_line:
            visualizer.draw_hints(surface, theme)
            self.assertGreater(mock_line.call_count, 0)


if __name__ == "__main__":
    unittest.main()
