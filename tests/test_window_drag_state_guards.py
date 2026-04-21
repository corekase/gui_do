import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class WindowDragStateGuardsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((400, 300))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_drag_capture_releases_when_window_hidden_mid_drag(self) -> None:
        win = self.root.add(WindowControl("win", Rect(40, 40, 200, 140), "W"))
        start = win.title_bar_rect().center

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.assertTrue(self.app.pointer_capture.is_owned_by("win"))

        win.visible = False
        self.assertIsNone(self.root._drag_window)
        self.assertIsNone(self.root._drag_last_pos)
        before = win.rect.topleft
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 20, start[1] + 10), "rel": (20, 10), "buttons": (1, 0, 0)},
            )
        )

        self.assertFalse(self.app.pointer_capture.is_owned_by("win"))
        self.assertEqual(win.rect.topleft, before)

    def test_drag_capture_releases_when_window_disabled_mid_drag(self) -> None:
        win = self.root.add(WindowControl("win", Rect(40, 40, 200, 140), "W"))
        start = win.title_bar_rect().center

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.assertTrue(self.app.pointer_capture.is_owned_by("win"))

        win.enabled = False
        self.assertIsNone(self.root._drag_window)
        self.assertIsNone(self.root._drag_last_pos)
        before = win.rect.topleft
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 20, start[1] + 10), "rel": (20, 10), "buttons": (1, 0, 0)},
            )
        )

        self.assertFalse(self.app.pointer_capture.is_owned_by("win"))
        self.assertEqual(win.rect.topleft, before)


if __name__ == "__main__":
    unittest.main()
