import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect, Surface

from gui_do.controls.image_control import ImageControl


class _DisabledFactory:
    def __init__(self) -> None:
        self.calls = 0

    def build_disabled_bitmap(self, idle_bitmap: Surface) -> Surface:
        self.calls += 1
        out = idle_bitmap.copy()
        out.fill((0, 0, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return out


class ImageControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((320, 200))

    def tearDown(self) -> None:
        pygame.quit()

    def test_relative_image_path_resolves_from_cwd(self) -> None:
        control = ImageControl("img", Rect(10, 10, 80, 40), "demo_features/data/images/realize.png", scale=False)
        target = Surface((200, 120), pygame.SRCALPHA)

        control.draw(target, SimpleNamespace(graphics_factory=_DisabledFactory()))
        self.assertGreater(control._base_image.get_width(), 0)
        self.assertGreater(control._base_image.get_height(), 0)

    def test_scale_true_recomputes_bitmap_when_rect_size_changes(self) -> None:
        source = Surface((4, 4), pygame.SRCALPHA)
        source.fill((200, 20, 20, 255))
        control = ImageControl("img", Rect(10, 10, 20, 20), source, scale=True)
        target = Surface((100, 100), pygame.SRCALPHA)

        control.draw(target, SimpleNamespace(graphics_factory=_DisabledFactory()))
        first = target.get_at((29, 29))

        control.rect.size = (40, 40)
        control.draw(target, SimpleNamespace(graphics_factory=_DisabledFactory()))
        second = target.get_at((49, 49))

        self.assertEqual(tuple(first[:3]), (200, 20, 20))
        self.assertEqual(tuple(second[:3]), (200, 20, 20))

    def test_disabled_draw_uses_disabled_bitmap_cache_and_hidden_draws_nothing(self) -> None:
        source = Surface((8, 8), pygame.SRCALPHA)
        source.fill((255, 255, 255, 255))
        control = ImageControl("img", Rect(10, 10, 20, 20), source, scale=True)
        factory = _DisabledFactory()
        theme = SimpleNamespace(graphics_factory=factory)
        target = Surface((120, 80), pygame.SRCALPHA)

        control.enabled = False
        control.draw(target, theme)
        control.draw(target, theme)

        self.assertEqual(factory.calls, 1)

        control.visible = False
        before = target.get_at((5, 5))
        control.draw(target, theme)
        after = target.get_at((5, 5))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
