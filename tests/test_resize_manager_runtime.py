import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import ResizeManager
from gui_do.layout.constraint_layout import ConstraintLayout, AnchorConstraint
from gui_do.controls.panel_control import PanelControl


class ResizeManagerRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.mgr = ResizeManager(initial_size=(800, 600))

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_initial_size(self) -> None:
        self.assertEqual(self.mgr.size, (800, 600))

    def test_width_height_properties(self) -> None:
        self.assertEqual(self.mgr.width, 800)
        self.assertEqual(self.mgr.height, 600)

    def test_initial_resize_count_zero(self) -> None:
        self.assertEqual(self.mgr.resize_count, 0)

    # ------------------------------------------------------------------
    # notify_resize
    # ------------------------------------------------------------------

    def test_notify_resize_updates_size(self) -> None:
        self.mgr.notify_resize(1024, 768)
        self.assertEqual(self.mgr.size, (1024, 768))

    def test_notify_resize_increments_count(self) -> None:
        self.mgr.notify_resize(100, 100)
        self.mgr.notify_resize(200, 200)
        self.assertEqual(self.mgr.resize_count, 2)

    def test_notify_resize_clamps_minimum(self) -> None:
        self.mgr.notify_resize(0, 0)
        self.assertEqual(self.mgr.size, (1, 1))

    def test_notify_resize_negative_clamped(self) -> None:
        self.mgr.notify_resize(-100, -50)
        self.assertEqual(self.mgr.size, (1, 1))

    # ------------------------------------------------------------------
    # on_resize callbacks
    # ------------------------------------------------------------------

    def test_on_resize_fires_callback(self) -> None:
        calls = []
        self.mgr.on_resize(lambda w, h: calls.append((w, h)))
        self.mgr.notify_resize(1280, 720)
        self.assertIn((1280, 720), calls)

    def test_on_resize_unsub_stops_callback(self) -> None:
        calls = []
        unsub = self.mgr.on_resize(lambda w, h: calls.append((w, h)))
        self.mgr.notify_resize(100, 100)
        unsub()
        self.mgr.notify_resize(200, 200)
        self.assertEqual(len(calls), 1)

    def test_on_resize_non_callable_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.mgr.on_resize("not_callable")  # type: ignore

    def test_multiple_callbacks_all_fired(self) -> None:
        calls_a = []
        calls_b = []
        self.mgr.on_resize(lambda w, h: calls_a.append((w, h)))
        self.mgr.on_resize(lambda w, h: calls_b.append((w, h)))
        self.mgr.notify_resize(640, 480)
        self.assertEqual(len(calls_a), 1)
        self.assertEqual(len(calls_b), 1)

    # ------------------------------------------------------------------
    # handle_pygame_event
    # ------------------------------------------------------------------

    def test_handle_pygame_event_videoresize(self) -> None:
        event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1920, "h": 1080})
        result = self.mgr.handle_pygame_event(event)
        self.assertTrue(result)
        self.assertEqual(self.mgr.size, (1920, 1080))

    def test_handle_pygame_event_other_returns_false(self) -> None:
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        result = self.mgr.handle_pygame_event(event)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # register_layout
    # ------------------------------------------------------------------

    def test_register_layout_applies_immediately(self) -> None:
        node = PanelControl("p", Rect(0, 0, 100, 100))
        layout = ConstraintLayout()
        layout.add(node, AnchorConstraint(left=0, top=0, right=0, bottom=0))
        self.mgr.register_layout(layout)
        self.assertEqual(node.rect.width, 800)
        self.assertEqual(node.rect.height, 600)

    def test_register_layout_reflows_on_resize(self) -> None:
        node = PanelControl("p", Rect(0, 0, 100, 100))
        layout = ConstraintLayout()
        layout.add(node, AnchorConstraint(left=0, top=0, right=0, bottom=0))
        self.mgr.register_layout(layout)
        self.mgr.notify_resize(1024, 768)
        self.assertEqual(node.rect.width, 1024)
        self.assertEqual(node.rect.height, 768)

    def test_unregister_layout_stops_reflow(self) -> None:
        node = PanelControl("p", Rect(0, 0, 100, 100))
        layout = ConstraintLayout()
        layout.add(node, AnchorConstraint(left=0, top=0, right=0, bottom=0))
        self.mgr.register_layout(layout)
        result = self.mgr.unregister_layout(layout)
        self.assertTrue(result)
        self.mgr.notify_resize(1024, 768)
        # Node size should not have changed to 1024 because layout was unregistered
        # (it was 800x600 from initial apply)
        self.assertEqual(node.rect.width, 800)

    def test_unregister_unknown_layout_returns_false(self) -> None:
        layout = ConstraintLayout()
        result = self.mgr.unregister_layout(layout)
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # EventBus integration
    # ------------------------------------------------------------------

    def test_event_bus_receives_window_resized(self) -> None:
        from gui_do.core.event_bus import EventBus
        bus = EventBus()
        received = []
        bus.subscribe("window_resized", lambda payload: received.append(payload))
        mgr = ResizeManager(initial_size=(800, 600), event_bus=bus)
        mgr.notify_resize(1280, 720)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], (1280, 720))


if __name__ == "__main__":
    unittest.main()
