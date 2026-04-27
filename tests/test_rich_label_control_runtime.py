import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import RichLabelControl, GuiApplication, PanelControl


class RichLabelControlRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((640, 480))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 640, 480)))

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_default_text_empty(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        self.assertEqual(ctrl.text, "")

    def test_initial_text_set(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), text="hello")
        self.assertEqual(ctrl.text, "hello")

    def test_default_font_role(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        self.assertEqual(ctrl.font_role, "body")

    def test_default_align(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        self.assertEqual(ctrl.align, "left")

    # ------------------------------------------------------------------
    # text property
    # ------------------------------------------------------------------

    def test_text_setter_updates(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        ctrl.text = "new text"
        self.assertEqual(ctrl.text, "new text")

    def test_text_setter_same_value_no_invalidate(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), text="same")
        ctrl._cache_key = "sentinel"
        ctrl.text = "same"
        # Cache key not cleared when value unchanged
        self.assertEqual(ctrl._cache_key, "sentinel")

    def test_text_setter_different_value_clears_cache(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), text="old")
        ctrl._cache_key = "sentinel"
        ctrl.text = "new"
        self.assertIsNone(ctrl._cache_key)

    # ------------------------------------------------------------------
    # font_role / font_size / align
    # ------------------------------------------------------------------

    def test_font_role_setter(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        ctrl.font_role = "title"
        self.assertEqual(ctrl.font_role, "title")

    def test_font_size_setter(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        ctrl.font_size = 24
        self.assertEqual(ctrl.font_size, 24)

    def test_font_size_minimum_clamped(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        ctrl.font_size = 0
        self.assertGreaterEqual(ctrl.font_size, 6)

    def test_align_left(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), align="left")
        self.assertEqual(ctrl.align, "left")

    def test_align_center(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), align="center")
        self.assertEqual(ctrl.align, "center")

    def test_align_right(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), align="right")
        self.assertEqual(ctrl.align, "right")

    def test_align_invalid_defaults_to_left(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200), align="bogus")
        self.assertEqual(ctrl.align, "left")

    # ------------------------------------------------------------------
    # Focus behaviour
    # ------------------------------------------------------------------

    def test_does_not_accept_mouse_focus(self) -> None:
        ctrl = RichLabelControl("rl", Rect(10, 10, 300, 200))
        self.assertFalse(ctrl.accepts_mouse_focus())

    # ------------------------------------------------------------------
    # Draw (smoke tests)
    # ------------------------------------------------------------------

    def test_draw_does_not_raise(self) -> None:
        ctrl = self.root.add(RichLabelControl("rl", Rect(10, 10, 300, 200), text="hello world"))
        self.app.draw()

    def test_draw_multiline_does_not_raise(self) -> None:
        ctrl = self.root.add(RichLabelControl("rl", Rect(10, 10, 300, 200), text="line one\nline two\nline three"))
        self.app.draw()

    def test_draw_long_text_clips_gracefully(self) -> None:
        long_text = "word " * 200
        ctrl = self.root.add(RichLabelControl("rl", Rect(10, 10, 300, 100), text=long_text))
        self.app.draw()

    def test_draw_empty_text_does_not_raise(self) -> None:
        ctrl = self.root.add(RichLabelControl("rl", Rect(10, 10, 300, 200), text=""))
        self.app.draw()


if __name__ == "__main__":
    unittest.main()
