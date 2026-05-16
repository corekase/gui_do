import types
import unittest

import pygame
from pygame import Rect

from gui_do.graphics.shear_window import ShearWindowController


pygame.init()


class _StubWindow:
    def __init__(self):
        self.rect = Rect(10, 10, 120, 80)


class TestShearWindowControllerReleaseRefresh(unittest.TestCase):
    def test_end_drag_defers_buffer_refresh_until_render(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        refresh_calls = []

        def fake_refresh(this, _surface, _theme, _draw_window_standard):
            refresh_calls.append(1)
            this.buffer = pygame.Surface(this.window.rect.size, pygame.SRCALPHA)

        controller._refresh_buffer = types.MethodType(fake_refresh, controller)

        controller.start_drag((40, 40), surface=None)
        controller.update_drag((56, 42))
        controller.end_drag((60, 43))

        self.assertEqual(0, len(refresh_calls))

        controller.render(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        self.assertEqual(1, len(refresh_calls))

    def test_settle_render_keeps_refreshing_live_content(self):
        window = _StubWindow()
        controller = ShearWindowController(window)
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)

        refresh_calls = []

        def fake_refresh(this, _surface, _theme, _draw_window_standard):
            refresh_calls.append(1)
            this.buffer = pygame.Surface(this.window.rect.size, pygame.SRCALPHA)

        controller._refresh_buffer = types.MethodType(fake_refresh, controller)

        controller.start_drag((40, 40), surface=None)
        controller.update_drag((58, 41))
        controller.end_drag((61, 42))

        controller.render(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        controller.render(surface, theme=object(), draw_window_standard=lambda _s, _t: None)

        self.assertGreaterEqual(len(refresh_calls), 2)


if __name__ == "__main__":
    unittest.main()
