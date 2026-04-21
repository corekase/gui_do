import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, LabelControl, PanelControl, WindowControl


class RebasedWindowFocusDragLayeringTest(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 500, 360)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_clicking_window_titlebar_sets_active_and_raises(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        self.assertEqual(self.root.children[-1], win_b)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": (30, 30),
                    "button": 1,
                },
            )
        )

        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)
        self.assertEqual(self.root.children[-1], win_a)

    def test_clicking_lower_widget_lowers_window(self) -> None:
        win_a = self.root.add(WindowControl("win_a", Rect(20, 20, 180, 140), "A"))
        win_b = self.root.add(WindowControl("win_b", Rect(120, 40, 180, 140), "B"))

        lower_pos = win_b.lower_widget_rect().center
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": lower_pos,
                    "button": 1,
                },
            )
        )

        self.assertEqual(self.root.children[0], win_b)

        # Clicking another window should make it active again.
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "pos": (30, 30),
                    "button": 1,
                },
            )
        )
        self.assertTrue(win_a.active)

    def test_titlebar_drag_moves_window_and_children(self) -> None:
        win = self.root.add(WindowControl("win", Rect(40, 40, 220, 160), "Drag"))
        child = win.add(LabelControl("child", Rect(56, 80, 100, 20), "child"))

        start_win_pos = win.rect.topleft
        start_child_pos = child.rect.topleft
        drag_start = (win.rect.left + 10, win.rect.top + 10)

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": drag_start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (drag_start[0] + 24, drag_start[1] + 18),
                    "rel": (24, 18),
                    "buttons": (1, 0, 0),
                },
            )
        )
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                {
                    "pos": (drag_start[0] + 24, drag_start[1] + 18),
                    "button": 1,
                },
            )
        )

        self.assertEqual(win.rect.topleft, (start_win_pos[0] + 24, start_win_pos[1] + 18))
        self.assertEqual(child.rect.topleft, (start_child_pos[0] + 24, start_child_pos[1] + 18))
        self.assertIsNone(self.app.pointer_capture.owner_id)


if __name__ == "__main__":
    unittest.main()
