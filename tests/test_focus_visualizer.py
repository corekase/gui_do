import unittest

import pygame
from pygame import Rect

from gui_do.focus.focus_visualizer import FocusVisualizer

pygame.init()


class _StubApp:
    pass


class _StubFocus:
    def __init__(self, focused_node):
        self.focused_node = focused_node

    def should_draw_focus_hint(self):
        return True


class _StubOverlay:
    def has_overlay(self, _overlay_id):
        return False


class _StubTheme:
    highlight = (255, 255, 255)


class _StubNode:
    def __init__(self, rect: Rect, parent=None):
        self.rect = Rect(rect)
        self.parent = parent
        self.visible = True

    def is_window(self):
        return False


class _StubWindow(_StubNode):
    def __init__(self, rect: Rect):
        super().__init__(rect)
        self.shear_active = False
        self.shear_controller = None

    def is_window(self):
        return True


class _StubShearController:
    def __init__(self, result=True):
        self.result = bool(result)
        self.called = 0
        self.last_overlay = None

    def blit_sheared_overlay(self, _surface, overlay):
        self.called += 1
        self.last_overlay = overlay.copy()
        return self.result


class TestFocusVisualizerDashedRectangle(unittest.TestCase):
    def test_dashed_rectangle_stays_within_box(self):
        surface = pygame.Surface((80, 60))
        surface.fill((0, 0, 0))

        visualizer = FocusVisualizer(_StubApp())
        visualizer._draw_dashed_rectangle(surface, Rect(20, 15, 30, 20), (255, 255, 255))

        # Top and bottom border rows should not extend past the hint box.
        self.assertEqual((0, 0, 0), surface.get_at((0, 15))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((79, 15))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((0, 34))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((79, 34))[:3])

        # Left and right border columns should not extend past the hint box.
        self.assertEqual((0, 0, 0), surface.get_at((20, 0))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((20, 59))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((49, 0))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((49, 59))[:3])

        # A point on the border should be painted.
        self.assertEqual((255, 255, 255), surface.get_at((20, 15))[:3])


class TestFocusVisualizerWindowShearHint(unittest.TestCase):
    def _build_visualizer(self, focused_node):
        app = _StubApp()
        app.focus = _StubFocus(focused_node)
        app.overlay = _StubOverlay()
        return FocusVisualizer(app)

    def test_draw_hint_for_window_delegates_to_shear_overlay(self):
        window = _StubWindow(Rect(10, 10, 80, 60))
        focused = _StubNode(Rect(20, 20, 10, 10), parent=window)
        shear = _StubShearController(result=True)
        window.shear_active = True
        window.shear_controller = shear

        visualizer = self._build_visualizer(focused)
        surface = pygame.Surface((160, 120))
        surface.fill((0, 0, 0))

        visualizer.draw_hint_for_window(surface, _StubTheme(), window)

        self.assertEqual(1, shear.called)
        self.assertIsNotNone(shear.last_overlay)
        # Focus rect is inflated by padding=2, then converted to window-local coordinates.
        self.assertEqual((255, 255, 255), shear.last_overlay.get_at((8, 8))[:3])

    def test_draw_hint_for_window_falls_back_to_direct_draw_without_shear(self):
        window = _StubWindow(Rect(10, 10, 80, 60))
        focused = _StubNode(Rect(20, 20, 10, 10), parent=window)

        visualizer = self._build_visualizer(focused)
        surface = pygame.Surface((160, 120))
        surface.fill((0, 0, 0))

        visualizer.draw_hint_for_window(surface, _StubTheme(), window)

        # Focus rect top-left in screen coordinates after padding inflation.
        self.assertEqual((255, 255, 255), surface.get_at((18, 18))[:3])


if __name__ == "__main__":
    unittest.main()
