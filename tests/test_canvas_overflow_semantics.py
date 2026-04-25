import unittest

import pygame
from pygame import Rect

from gui.controls.canvas_control import CanvasControl
from gui.core.gui_event import EventType, GuiEvent


def _motion(pos):
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=pos, rel=(0, 0))


class CanvasOverflowSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_drop_newest_reports_drops_until_next_successful_enqueue(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 10, 10), max_events=1)
        control.set_motion_coalescing(False)
        control.set_overflow_mode("drop_newest")
        seen = []
        control.set_overflow_handler(lambda dropped, queued: seen.append((dropped, queued)))

        self.assertTrue(control.handle_event(_motion((1, 1)), None))
        self.assertEqual(seen, [])

        self.assertTrue(control.handle_event(_motion((2, 2)), None))
        self.assertTrue(control.handle_event(_motion((3, 3)), None))
        self.assertEqual(seen, [(1, 1), (2, 1)])

        _ = control.read_event()
        self.assertTrue(control.handle_event(_motion((4, 4)), None))
        self.assertEqual(seen, [(1, 1), (2, 1)])

        self.assertTrue(control.handle_event(_motion((5, 5)), None))
        self.assertEqual(seen, [(1, 1), (2, 1), (1, 1)])

    def test_coalesced_motion_clears_pending_drop_count(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 10, 10), max_events=1)
        control.set_motion_coalescing(False)
        control.set_overflow_mode("drop_newest")

        self.assertTrue(control.handle_event(_motion((1, 1)), None))
        self.assertTrue(control.handle_event(_motion((2, 2)), None))

        control.set_motion_coalescing(True)
        self.assertTrue(control.handle_event(_motion((3, 3)), None))

        _ = control.read_event()
        seen = []
        control.set_overflow_handler(lambda dropped, queued: seen.append((dropped, queued)))

        self.assertTrue(control.handle_event(_motion((4, 4)), None))
        self.assertEqual(seen, [])

    def test_drop_oldest_reports_each_drop_and_keeps_latest_event(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 10, 10), max_events=1)
        control.set_motion_coalescing(False)
        control.set_overflow_mode("drop_oldest")
        seen = []
        control.set_overflow_handler(lambda dropped, queued: seen.append((dropped, queued)))

        self.assertTrue(control.handle_event(_motion((1, 1)), None))
        self.assertEqual(seen, [])

        self.assertTrue(control.handle_event(_motion((2, 2)), None))
        self.assertEqual(seen, [(1, 1)])

        queued = control.read_event()
        self.assertIsNotNone(queued)
        self.assertEqual(queued.pos, (2, 2))

        self.assertTrue(control.handle_event(_motion((3, 3)), None))
        self.assertTrue(control.handle_event(_motion((4, 4)), None))
        self.assertEqual(seen, [(1, 1), (1, 1)])


if __name__ == "__main__":
    unittest.main()
