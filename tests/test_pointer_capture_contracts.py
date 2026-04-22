import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, LayoutAxis, PanelControl, ScrollbarControl, SliderControl


class PointerCaptureContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((420, 300))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 420, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_slider_drag_release_clears_capture_and_keeps_value(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start_center = slider.handle_rect().center

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start_center, "button": 1}))
        self.assertTrue(slider.dragging)
        self.assertTrue(self.app.pointer_capture.is_owned_by("slider"))

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (start_center[0] + 60, start_center[1] + 999),
                    "rel": (60, 999),
                    "buttons": (1, 0, 0),
                },
            )
        )
        during_value = slider.value

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                {"pos": (start_center[0] + 60, start_center[1] + 999), "button": 1},
            )
        )

        self.assertFalse(slider.dragging)
        self.assertIsNone(self.app.pointer_capture.owner_id)
        self.assertEqual(during_value, slider.value)

    def test_scrollbar_drag_release_clears_capture_and_keeps_offset(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start_center = scrollbar.handle_rect().center

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start_center, "button": 1}))
        self.assertTrue(scrollbar.dragging)
        self.assertTrue(self.app.pointer_capture.is_owned_by("scroll"))

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (start_center[0] + 70, start_center[1] + 999),
                    "rel": (70, 999),
                    "buttons": (1, 0, 0),
                },
            )
        )
        during_offset = scrollbar.offset

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                {"pos": (start_center[0] + 70, start_center[1] + 999), "button": 1},
            )
        )

        self.assertFalse(scrollbar.dragging)
        self.assertIsNone(self.app.pointer_capture.owner_id)
        self.assertEqual(during_offset, scrollbar.offset)


if __name__ == "__main__":
    unittest.main()
