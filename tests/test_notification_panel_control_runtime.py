import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do.controls.notification_panel_control import NotificationPanelControl
from gui_do.core.gui_event import EventType
from gui_do.core.notification_center import NotificationCenter, NotificationRecord
from gui_do.core.pointer_capture import PointerCapture


class NotificationPanelControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((360, 240))

    def tearDown(self) -> None:
        pygame.quit()

    def test_dragging_scrollbar_thumb_updates_scroll_offset(self) -> None:
        center = NotificationCenter(None, max_records=64)
        for i in range(20):
            center.add(NotificationRecord(f"message {i}"))
        panel = NotificationPanelControl("np", Rect(20, 20, 220, 180), center)

        handle = panel._scrollbar_handle_rect()
        self.assertIsNotNone(handle)
        handle = handle

        class _AppStub:
            def __init__(self):
                self.logical_pointer_pos = (0, 0)
                self.pointer_capture = PointerCapture()
                self.synced_pointer_pos = None

            def set_logical_pointer_position(self, pos, apply_constraints=True):
                self.logical_pointer_pos = (int(pos[0]), int(pos[1]))

            def sync_pointer_to_logical_position(self, pos):
                self.synced_pointer_pos = (int(pos[0]), int(pos[1]))

        app = _AppStub()

        down = MagicMock()
        down.kind = EventType.MOUSE_BUTTON_DOWN
        down.button = 1
        down.pos = handle.center
        down.wheel_delta = 0

        move = MagicMock()
        move.kind = EventType.MOUSE_MOTION
        move.button = None
        move.pos = (handle.centerx, min(panel.rect.bottom - 4, handle.centery + 36))
        move.wheel_delta = 0

        up = MagicMock()
        up.kind = EventType.MOUSE_BUTTON_UP
        up.button = 1
        up.pos = move.pos
        up.wheel_delta = 0

        initial = panel._scroll_offset
        self.assertTrue(panel.handle_event(down, app))
        self.assertTrue(app.pointer_capture.is_owned_by("np"))

        app.logical_pointer_pos = move.pos
        self.assertTrue(panel.handle_event(move, app))
        self.assertGreater(panel._scroll_offset, initial)

        self.assertTrue(panel.handle_event(up, app))
        self.assertFalse(app.pointer_capture.is_owned_by("np"))
        self.assertIsNotNone(app.synced_pointer_pos)


if __name__ == "__main__":
    unittest.main()
