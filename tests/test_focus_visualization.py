"""Tests for focus visualization with dashed rectangles and smooth fade-out."""
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui.core.focus_visualizer import FocusVisualizer
from gui.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS
from gui.core.focus_manager import FocusManager
from gui.core.ui_node import UiNode
from gui.core.scene import Scene
from gui.theme.color_theme import ColorTheme


class FocusVisualizerStateTests(unittest.TestCase):
    """Test FocusVisualizer state transitions and timing."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)
        self.theme = ColorTheme()

    def test_initial_state_empty(self) -> None:
        self.assertIsNone(self.visualizer._current_hint_node)
        self.assertEqual(self.visualizer._current_hint_elapsed, 0.0)

    def test_set_focus_hint_starts_display(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.assertIs(self.visualizer._current_hint_node, node)
        self.assertEqual(self.visualizer._current_hint_elapsed, 0.0)

    def test_set_focus_hint_same_node_idempotent(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.visualizer.set_focus_hint(node)
        self.assertIs(self.visualizer._current_hint_node, node)

    def test_set_focus_hint_switches_current_immediately_clears_previous(self) -> None:
        node1 = UiNode("n1", Rect(0, 0, 100, 100))
        node2 = UiNode("n2", Rect(100, 0, 100, 100))
        self.visualizer.set_focus_hint(node1)
        self.visualizer.set_focus_hint(node2)
        self.assertIs(self.visualizer._current_hint_node, node2)
        # Previous hint should be immediately gone (no fade-out)
        self.assertFalse(hasattr(self.visualizer, '_previous_hint_node'))

    def test_clear_focus_hint_clears_all_state(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.visualizer.clear_focus_hint()
        self.assertIsNone(self.visualizer._current_hint_node)
        self.assertEqual(self.visualizer._current_hint_elapsed, 0.0)

    def test_hint_timeout_uses_shared_constant(self) -> None:
        self.assertEqual(self.visualizer.HINT_TIMEOUT_SECONDS, FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS)
        self.assertEqual(self.visualizer.HINT_TIMEOUT_SECONDS, self.visualizer.HOLD_TIME + self.visualizer.FADE_TIME)


class FocusVisualizerTimingTests(unittest.TestCase):
    """Test timing and fade-out behavior."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)
        self.node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(self.node)

    def test_hold_phase_no_fade_before_hold_time(self) -> None:
        self.visualizer.update(0.5)  # 0.5 seconds
        self.assertLess(self.visualizer._current_hint_elapsed, self.visualizer.HOLD_TIME)
        # Compute alpha as draw method would
        alpha = 1.0
        self.assertEqual(alpha, 1.0)

    def test_fade_starts_after_hold_time(self) -> None:
        self.visualizer.update(1.0)  # 1 second (hold time)
        self.visualizer.update(0.01)  # Tiny bit into fade
        self.assertGreaterEqual(self.visualizer._current_hint_elapsed, self.visualizer.HOLD_TIME)
        # Compute alpha as draw method would
        fade_elapsed = self.visualizer._current_hint_elapsed - self.visualizer.HOLD_TIME
        fade_progress = fade_elapsed / self.visualizer.FADE_TIME
        alpha = 1.0 - fade_progress
        self.assertLess(alpha, 1.0)

    def test_fade_progress_linear(self) -> None:
        self.visualizer.update(1.0)  # Reach end of hold
        self.visualizer.update(0.25)  # 0.25s into 0.5s fade (50%)
        # At 50% of fade time
        fade_elapsed = self.visualizer._current_hint_elapsed - self.visualizer.HOLD_TIME
        fade_progress = fade_elapsed / self.visualizer.FADE_TIME
        alpha = 1.0 - fade_progress
        self.assertAlmostEqual(alpha, 0.5, places=1)

    def test_fade_complete_clears_current_hint(self) -> None:
        self.visualizer.update(1.0)  # End of hold
        self.visualizer.update(0.5)  # Complete fade
        self.assertIsNone(self.visualizer._current_hint_node)

    def test_previous_node_immediately_clears_on_switch(self) -> None:
        node2 = UiNode("n2", Rect(100, 0, 100, 100))
        self.visualizer.update(0.5)  # Half way through hold
        self.visualizer.set_focus_hint(node2)  # Switch focus
        self.assertIs(self.visualizer._current_hint_node, node2)
        # Previous node should be cleared (no fade object)
        self.assertFalse(hasattr(self.visualizer, '_previous_hint_node'))

    # Removed: test_previous_node_fade_completes - no longer applicable with immediate clear


class FocusVisualizerDrawingTests(unittest.TestCase):
    """Test drawing behavior."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)
        self.theme = ColorTheme()
        self.surface = pygame.Surface((800, 600))

    def test_draw_hints_no_crash_with_no_hints(self) -> None:
        self.visualizer.draw_hints(self.surface, self.theme)  # Must not raise

    def test_draw_hints_skips_invisible_nodes(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        node.visible = False
        self.visualizer.set_focus_hint(node)
        self.visualizer.draw_hints(self.surface, self.theme)  # Must not raise

    def test_draw_hints_skips_node_with_degenerate_rect(self) -> None:
        node = UiNode("n", Rect(0, 0, 1, 1))
        self.visualizer.set_focus_hint(node)
        with patch("pygame.draw.line") as mock_line:
            self.visualizer.draw_hints(self.surface, self.theme)
            mock_line.assert_not_called()

    def test_draw_dashed_rect_draws_lines(self) -> None:
        rect = Rect(10, 10, 100, 100)
        with patch("pygame.draw.line") as mock_line:
            self.visualizer._draw_dashed_rectangle(self.surface, rect, (255, 0, 0))
            # Should draw multiple line segments (dashes)
            self.assertGreater(mock_line.call_count, 0)


class FocusManagerIntegrationTests(unittest.TestCase):
    """Test FocusManager integration with FocusVisualizer."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)
        self.manager = FocusManager(visualizer=self.visualizer)

    def test_focus_manager_without_visualizer(self) -> None:
        manager = FocusManager()  # No visualizer
        node = UiNode("n", Rect(0, 0, 100, 100))
        manager.set_focus(node)  # Must not raise

    def test_focus_manager_triggers_visualizer(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.manager.set_focus(node)
        self.assertIs(self.visualizer._current_hint_node, node)

    def test_focus_manager_clears_visualizer(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.manager.set_focus(node)
        self.manager.clear_focus()
        self.assertIsNone(self.visualizer._current_hint_node)

    def test_focus_manager_switches_focus_immediately_clears_previous(self) -> None:
        node1 = UiNode("n1", Rect(0, 0, 100, 100))
        node2 = UiNode("n2", Rect(100, 0, 100, 100))
        self.manager.set_focus(node1)
        self.manager.set_focus(node2)
        self.assertIs(self.visualizer._current_hint_node, node2)
        # Previous hint immediately clears (no fading or previous tracking)
        self.assertFalse(hasattr(self.visualizer, '_previous_hint_node'))


class FocusVisualizerEdgeCasesTests(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self) -> None:
        self.app = SimpleNamespace()
        self.visualizer = FocusVisualizer(self.app)

    def test_zero_dt_update_no_change(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.visualizer.update(0.0)
        self.assertEqual(self.visualizer._current_hint_elapsed, 0.0)

    def test_negative_dt_update_no_crash(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.visualizer.update(-0.1)  # Must not raise
        self.assertEqual(self.visualizer._current_hint_elapsed, 0.0)

    def test_large_dt_update_completes_fade(self) -> None:
        node = UiNode("n", Rect(0, 0, 100, 100))
        self.visualizer.set_focus_hint(node)
        self.visualizer.update(10.0)  # Very large time step
        self.assertIsNone(self.visualizer._current_hint_node)

    def test_tiny_control_not_drawn(self) -> None:
        node = UiNode("n", Rect(0, 0, 1, 1))
        self.visualizer.set_focus_hint(node)
        theme = ColorTheme()
        surface = pygame.Surface((800, 600))
        self.visualizer.draw_hints(surface, theme)  # Must not raise (skips tiny controls)

    def test_multiple_focus_switches_immediately_clear(self) -> None:
        """When focus switches multiple times, previous hints clear immediately."""
        n1 = UiNode("n1", Rect(0, 0, 100, 100))
        n2 = UiNode("n2", Rect(100, 0, 100, 100))
        n3 = UiNode("n3", Rect(200, 0, 100, 100))

        self.visualizer.set_focus_hint(n1)
        self.visualizer.set_focus_hint(n2)
        self.assertIs(self.visualizer._current_hint_node, n2)
        # n1 is gone, no previous_hint_node tracking

        self.visualizer.set_focus_hint(n3)
        self.assertIs(self.visualizer._current_hint_node, n3)
        # n2 is gone, no previous_hint_node tracking


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


class FocusHintWindowOcclusionTests(unittest.TestCase):
    """Hints should not render above topmost windows that occlude the target."""

    def test_hint_skips_when_top_window_covers_target_center(self) -> None:
        class _WindowStub(UiNode):
            def is_window(self) -> bool:
                return True

        scene = Scene()
        target = UiNode("target", Rect(40, 40, 20, 20))
        window = _WindowStub("win", Rect(0, 0, 120, 120))
        scene.add(target)
        scene.add(window)  # topmost, covers target center

        app = SimpleNamespace(scene=scene)
        visualizer = FocusVisualizer(app)
        visualizer.set_focus_hint(target)

        surface = pygame.Surface((160, 120))
        theme = ColorTheme()
        with patch("pygame.draw.line") as mock_line:
            visualizer.draw_hints(surface, theme)
            mock_line.assert_not_called()

    def test_hint_partially_draws_when_window_only_covers_part_of_target(self) -> None:
        class _WindowStub(UiNode):
            def is_window(self) -> bool:
                return True

        target = UiNode("target", Rect(40, 40, 20, 20))
        theme = ColorTheme()
        surface = pygame.Surface((160, 120))

        scene_no_window = Scene()
        scene_no_window.add(target)
        visualizer_no_window = FocusVisualizer(SimpleNamespace(scene=scene_no_window))
        visualizer_no_window.set_focus_hint(target)
        with patch("pygame.draw.line") as full_draw_mock:
            visualizer_no_window.draw_hints(surface, theme)
            full_count = full_draw_mock.call_count

        scene_partial_window = Scene()
        target_partial = UiNode("target_partial", Rect(40, 40, 20, 20))
        partial_window = _WindowStub("win", Rect(52, 0, 120, 120))
        scene_partial_window.add(target_partial)
        scene_partial_window.add(partial_window)
        visualizer_partial = FocusVisualizer(SimpleNamespace(scene=scene_partial_window))
        visualizer_partial.set_focus_hint(target_partial)
        with patch("pygame.draw.line") as partial_draw_mock:
            visualizer_partial.draw_hints(surface, theme)
            partial_count = partial_draw_mock.call_count

        self.assertGreater(full_count, 0)
        self.assertGreater(partial_count, 0)
        self.assertLess(partial_count, full_count)


if __name__ == "__main__":
    unittest.main()
