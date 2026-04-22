import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect, Surface

from gui.controls.label_control import LabelControl


class _FakeTheme:
    def __init__(self) -> None:
        self.text = (10, 20, 30)
        self.medium = (80, 90, 100)
        self.last_call = None

    def render_text(self, text: str, size: int = 16, title: bool = False, color=None, shadow: bool = True):
        self.last_call = {
            "text": text,
            "size": size,
            "title": title,
            "color": color,
            "shadow": shadow,
        }
        surface = Surface((20, 10), pygame.SRCALPHA)
        surface.fill((255, 255, 255, 255))
        return surface


class LabelControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((240, 140))

    def tearDown(self) -> None:
        pygame.quit()

    def test_draw_uses_text_size_and_title_flags(self) -> None:
        label = LabelControl("lbl", Rect(10, 10, 100, 20), "Hello")
        label.text_size = 24
        label.title = True
        theme = _FakeTheme()
        target = Surface((120, 80), pygame.SRCALPHA)

        label.draw(target, theme)

        self.assertIsNotNone(theme.last_call)
        self.assertEqual(theme.last_call["text"], "Hello")
        self.assertEqual(theme.last_call["size"], 24)
        self.assertTrue(theme.last_call["title"])
        self.assertEqual(theme.last_call["color"], theme.text)

    def test_disabled_label_uses_medium_colour(self) -> None:
        label = LabelControl("lbl", Rect(10, 10, 100, 20), "Hello")
        label.enabled = False
        theme = _FakeTheme()
        target = Surface((120, 80), pygame.SRCALPHA)

        label.draw(target, theme)

        self.assertEqual(theme.last_call["color"], theme.medium)

    def test_runtime_property_updates_invalidate(self) -> None:
        label = LabelControl("lbl", Rect(10, 10, 100, 20), "Hello")
        label.clear_dirty()
        self.assertFalse(label.dirty)

        label.text = "Changed"
        self.assertTrue(label.dirty)

        label.clear_dirty()
        label.title = True
        self.assertTrue(label.dirty)

        label.clear_dirty()
        label.text_size = 22
        self.assertTrue(label.dirty)


if __name__ == "__main__":
    unittest.main()
