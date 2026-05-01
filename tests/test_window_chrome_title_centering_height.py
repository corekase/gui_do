import unittest

import pygame

from gui_do.graphics.built_in_factory import BuiltInGraphicsFactory
from gui_do.theme.font_manager import FontManager


class _ThemeStub:
    def __init__(self, fonts):
        self.fonts = fonts
        self.text = (255, 255, 255)
        self.highlight = (255, 255, 0)
        self.shadow = (0, 0, 0)


class TestWindowChromeTitleCenteringHeight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_build_window_chrome_respects_requested_titlebar_height(self):
        fonts = FontManager()
        fonts.register_role("title", size=16)
        theme = _ThemeStub(fonts)
        factory = BuiltInGraphicsFactory(theme)

        visuals = factory.build_window_chrome_visuals(
            width=320,
            titlebar_height=60,
            title="Window",
            title_font_role="title",
        )

        self.assertEqual(60, visuals.title_bar_active.get_height())
        self.assertEqual(60, visuals.title_bar_inactive.get_height())

    def test_build_window_chrome_enforces_minimum_height_for_font(self):
        fonts = FontManager()
        fonts.register_role("title", size=36)
        theme = _ThemeStub(fonts)
        factory = BuiltInGraphicsFactory(theme)

        visuals = factory.build_window_chrome_visuals(
            width=320,
            titlebar_height=10,
            title="Window",
            title_font_role="title",
        )

        self.assertGreaterEqual(visuals.title_bar_active.get_height(), 14)
        self.assertGreater(visuals.title_bar_active.get_height(), 10)


if __name__ == "__main__":
    unittest.main()
