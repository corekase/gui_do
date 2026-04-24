import os
import unittest
from unittest.mock import patch

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

    def test_slider_drag_release_syncs_hardware_to_final_logical_position(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_release_sync",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start_center = slider.handle_rect().center

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start_center, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (slider._travel_rect().right + 500, start_center[1]),
                    "rel": (500, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        expected_release = self.app.logical_pointer_pos

        with patch("pygame.mouse.set_pos") as set_pos_mock:
            self.app.process_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONUP,
                    {"pos": (slider._travel_rect().right + 500, start_center[1]), "button": 1},
                )
            )

        set_pos_mock.assert_called_once_with(expected_release)
        self.assertEqual(self.app.logical_pointer_pos, expected_release)

    def test_scrollbar_drag_release_syncs_hardware_to_final_logical_position(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_release_sync",
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
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (scrollbar._track_rect().right + 500, start_center[1]),
                    "rel": (500, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        expected_release = self.app.logical_pointer_pos

        with patch("pygame.mouse.set_pos") as set_pos_mock:
            self.app.process_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONUP,
                    {"pos": (scrollbar._track_rect().right + 500, start_center[1]), "button": 1},
                )
            )

        set_pos_mock.assert_called_once_with(expected_release)
        self.assertEqual(self.app.logical_pointer_pos, expected_release)

    def test_slider_drag_lock_area_bounds_are_handle_accounted_horizontal(self) -> None:
        self.app.set_lock_area(Rect(0, 0, 180, 120))
        slider = self.root.add(
            SliderControl(
                "slider_lock_h",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        handle = slider.handle_rect()
        down_pos = (handle.right - 1, handle.centery)
        anchor = down_pos[0] - handle.x
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": down_pos, "button": 1}))

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (slider._travel_rect().right + 500, down_pos[1]),
                    "rel": (500, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )

        expected_pointer = (self.app.lock_area.right - slider.handle_size) + anchor
        self.assertEqual(self.app.logical_pointer_pos[0], expected_pointer)

    def test_slider_drag_lock_area_bounds_are_handle_accounted_vertical(self) -> None:
        self.app.set_lock_area(Rect(0, 0, 220, 180))
        slider = self.root.add(
            SliderControl(
                "slider_lock_v",
                Rect(280, 20, 24, 220),
                LayoutAxis.VERTICAL,
                0.0,
                100.0,
                50.0,
            )
        )
        handle = slider.handle_rect()
        down_pos = (handle.centerx, handle.bottom - 1)
        anchor = down_pos[1] - handle.y
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": down_pos, "button": 1}))

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (down_pos[0], slider._travel_rect().bottom + 600),
                    "rel": (0, 600),
                    "buttons": (1, 0, 0),
                },
            )
        )

        expected_pointer = (self.app.lock_area.bottom - slider.handle_size) + anchor
        self.assertEqual(self.app.logical_pointer_pos[1], expected_pointer)

    def test_scrollbar_drag_lock_area_bounds_are_handle_accounted_horizontal(self) -> None:
        self.app.set_lock_area(Rect(0, 0, 180, 140))
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_lock_h",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        handle = scrollbar.handle_rect()
        down_pos = (handle.right - 1, handle.centery)
        anchor = down_pos[0] - handle.x
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": down_pos, "button": 1}))

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (scrollbar._track_rect().right + 700, down_pos[1]),
                    "rel": (700, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )

        expected_pointer = (self.app.lock_area.right - scrollbar._handle_length()) + anchor
        self.assertEqual(self.app.logical_pointer_pos[0], expected_pointer)

    def test_scrollbar_drag_lock_area_bounds_are_handle_accounted_vertical(self) -> None:
        self.app.set_lock_area(Rect(0, 0, 240, 180))
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_lock_v",
                Rect(320, 20, 24, 220),
                LayoutAxis.VERTICAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        handle = scrollbar.handle_rect()
        down_pos = (handle.centerx, handle.bottom - 1)
        anchor = down_pos[1] - handle.y
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": down_pos, "button": 1}))

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (down_pos[0], scrollbar._track_rect().bottom + 700),
                    "rel": (0, 700),
                    "buttons": (1, 0, 0),
                },
            )
        )

        expected_pointer = (self.app.lock_area.bottom - scrollbar._handle_length()) + anchor
        self.assertEqual(self.app.logical_pointer_pos[1], expected_pointer)

    def test_slider_drag_responds_to_runtime_lock_area_changes(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_runtime_lock",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        handle = slider.handle_rect()
        down_pos = (handle.right - 1, handle.centery)
        anchor = down_pos[0] - handle.x
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": down_pos, "button": 1}))

        self.app.set_lock_area(Rect(0, 0, 140, 120))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (slider._travel_rect().right + 400, down_pos[1]),
                    "rel": (400, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        expected_pointer = (self.app.lock_area.right - slider.handle_size) + anchor
        self.assertEqual(self.app.logical_pointer_pos[0], expected_pointer)

    def test_scrollbar_drag_responds_to_runtime_lock_area_changes(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_runtime_lock",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        handle = scrollbar.handle_rect()
        down_pos = (handle.right - 1, handle.centery)
        anchor = down_pos[0] - handle.x
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": down_pos, "button": 1}))

        self.app.set_lock_area(Rect(0, 0, 150, 160))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (scrollbar._track_rect().right + 450, down_pos[1]),
                    "rel": (450, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        expected_pointer = (self.app.lock_area.right - scrollbar._handle_length()) + anchor
        self.assertEqual(self.app.logical_pointer_pos[0], expected_pointer)

    def test_slider_reverse_from_max_overshoot_has_no_movement_debt(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_reverse_no_debt",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        travel = slider._travel_rect()

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (travel.right + 800, start[1]),
                    "rel": (800, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        self.assertEqual(slider.value, slider.maximum)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (travel.right + 799, start[1]),
                    "rel": (-1, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        self.assertLess(slider.value, slider.maximum)

    def test_scrollbar_reverse_from_max_overshoot_has_no_movement_debt(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_reverse_no_debt",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        track = scrollbar._track_rect()

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (track.right + 800, start[1]),
                    "rel": (800, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        self.assertEqual(scrollbar.offset, scrollbar._max_offset())

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {
                    "pos": (track.right + 799, start[1]),
                    "rel": (-1, 0),
                    "buttons": (1, 0, 0),
                },
            )
        )
        self.assertLess(scrollbar.offset, scrollbar._max_offset())

    def test_slider_programmatic_set_value_ends_drag(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_programmatic_cancel",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.assertTrue(slider.dragging)

        slider.set_value(10.0)
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 5, start[1]), "rel": (5, 0), "buttons": (1, 0, 0)},
            )
        )

        self.assertFalse(slider.dragging)
        self.assertIsNone(self.app.pointer_capture.owner_id)

    def test_scrollbar_programmatic_set_offset_ends_drag(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_programmatic_cancel",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.assertTrue(scrollbar.dragging)

        scrollbar.set_offset(40)
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 5, start[1]), "rel": (5, 0), "buttons": (1, 0, 0)},
            )
        )

        self.assertFalse(scrollbar.dragging)
        self.assertIsNone(self.app.pointer_capture.owner_id)

    def test_slider_release_ignores_first_stale_motion_packet(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_release_stale_motion",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 80, start[1]), "rel": (80, 0), "buttons": (1, 0, 0)},
            )
        )
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (start[0] + 80, start[1]), "button": 1}))
        release_pos = self.app.logical_pointer_pos

        # Simulate one stale packet with old raw position that should be ignored.
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (release_pos[0] + 400, release_pos[1] + 200), "rel": (0, 0), "buttons": (0, 0, 0)},
            )
        )
        self.assertEqual(self.app.logical_pointer_pos, release_pos)

        # Simulate additional queued stale packet(s) after release.
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (release_pos[0] + 350, release_pos[1] + 180), "rel": (0, 0), "buttons": (0, 0, 0)},
            )
        )
        self.assertEqual(self.app.logical_pointer_pos, release_pos)

    def test_scrollbar_release_ignores_first_stale_motion_packet(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_release_stale_motion",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (start[0] + 90, start[1]), "rel": (90, 0), "buttons": (1, 0, 0)},
            )
        )
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (start[0] + 90, start[1]), "button": 1}))
        release_pos = self.app.logical_pointer_pos

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (release_pos[0] - 350, release_pos[1] + 150), "rel": (0, 0), "buttons": (0, 0, 0)},
            )
        )
        self.assertEqual(self.app.logical_pointer_pos, release_pos)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (release_pos[0] - 300, release_pos[1] + 120), "rel": (0, 0), "buttons": (0, 0, 0)},
            )
        )
        self.assertEqual(self.app.logical_pointer_pos, release_pos)

    def test_slider_outside_then_reenter_remains_continuous_without_snap(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_reenter_anchor",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        travel = slider._travel_rect()

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (travel.right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )

        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        reenter_pos = (int(lock.right - 2), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": reenter_pos, "rel": (-920, 0), "buttons": (1, 0, 0)},
            )
        )

        self.assertLess(self.app.logical_pointer_pos[0], lock.right)
        self.assertGreaterEqual(self.app.logical_pointer_pos[0], lock.left)

    def test_scrollbar_outside_then_reenter_remains_continuous_without_snap(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_reenter_anchor",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        track = scrollbar._track_rect()

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (track.right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )

        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        reenter_pos = (int(lock.right - 2), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": reenter_pos, "rel": (-920, 0), "buttons": (1, 0, 0)},
            )
        )

        self.assertLess(self.app.logical_pointer_pos[0], lock.right)
        self.assertGreaterEqual(self.app.logical_pointer_pos[0], lock.left)

    def test_slider_release_uses_mouse_up_in_range_after_overshoot(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_release_reentry",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (slider._travel_rect().right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )
        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        release_pos = (int(lock.right - 2), start[1])
        before_release = self.app.logical_pointer_pos

        # No in-range motion event before mouse-up; mouse-up must preserve the
        # current logical drag position (no drag-end jump).
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": release_pos, "button": 1}))

        self.assertEqual(self.app.logical_pointer_pos, before_release)
        self.assertEqual(slider.value, slider.maximum)

    def test_scrollbar_release_uses_mouse_up_in_range_after_overshoot(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_release_reentry",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (scrollbar._track_rect().right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )
        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        release_pos = (int(lock.right - 2), start[1])
        before_release = self.app.logical_pointer_pos

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": release_pos, "button": 1}))

        self.assertEqual(self.app.logical_pointer_pos, before_release)
        self.assertEqual(scrollbar.offset, scrollbar._max_offset())

    def test_slider_handle_rect_tracks_live_drag_axis_without_jitter(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_handle_tracks",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (slider._travel_rect().right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )
        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        reenter = (int(lock.right - 2), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": reenter, "rel": (-920, 0), "buttons": (1, 0, 0)},
            )
        )
        handle = slider.handle_rect()
        self.assertEqual(handle.x + slider._drag_anchor_offset, self.app.logical_pointer_pos[0])

    def test_scrollbar_handle_rect_tracks_live_drag_axis_without_jitter(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_handle_tracks",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (scrollbar._track_rect().right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )
        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        reenter = (int(lock.right - 2), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": reenter, "rel": (-920, 0), "buttons": (1, 0, 0)},
            )
        )
        handle = scrollbar.handle_rect()
        self.assertEqual(handle.x + scrollbar._drag_anchor_offset, self.app.logical_pointer_pos[0])

    def test_slider_pointer_position_is_drag_value_source_after_reentry(self) -> None:
        slider = self.root.add(
            SliderControl(
                "slider_pointer_source",
                Rect(20, 20, 220, 32),
                LayoutAxis.HORIZONTAL,
                0.0,
                100.0,
                50.0,
            )
        )
        start = slider.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (slider._travel_rect().right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )

        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        reenter = (int(lock.right - 2), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": reenter, "rel": (-920, 0), "buttons": (1, 0, 0)},
            )
        )
        val_after_reenter = slider.value

        deeper_in_range = (int(lock.right - 14), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": deeper_in_range, "rel": (-12, 0), "buttons": (1, 0, 0)},
            )
        )

        expected_axis = self.app.logical_pointer_pos[0] - slider._drag_anchor_offset + (slider.handle_size // 2)
        expected_value = slider._to_value(expected_axis)
        handle = slider.handle_rect()
        self.assertEqual(handle.x + slider._drag_anchor_offset, self.app.logical_pointer_pos[0])
        self.assertAlmostEqual(slider.value, expected_value)
        self.assertLessEqual(slider.value, val_after_reenter)

    def test_scrollbar_pointer_position_is_drag_value_source_after_reentry(self) -> None:
        scrollbar = self.root.add(
            ScrollbarControl(
                "scroll_pointer_source",
                Rect(20, 80, 220, 24),
                LayoutAxis.HORIZONTAL,
                content_size=2000,
                viewport_size=500,
                offset=300,
                step=10,
            )
        )
        start = scrollbar.handle_rect().center
        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (scrollbar._track_rect().right + 900, start[1]), "rel": (900, 0), "buttons": (1, 0, 0)},
            )
        )

        lock = self.app.pointer_capture.lock_rect
        self.assertIsNotNone(lock)
        reenter = (int(lock.right - 2), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": reenter, "rel": (-920, 0), "buttons": (1, 0, 0)},
            )
        )
        offset_after_reenter = scrollbar.offset

        deeper_in_range = (int(lock.right - 14), start[1])
        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": deeper_in_range, "rel": (-12, 0), "buttons": (1, 0, 0)},
            )
        )

        track = scrollbar._track_rect()
        expected_axis = self.app.logical_pointer_pos[0] - track.left - scrollbar._drag_anchor_offset
        expected_offset = scrollbar._pixel_to_offset(expected_axis)
        handle = scrollbar.handle_rect()
        self.assertEqual(handle.x + scrollbar._drag_anchor_offset, self.app.logical_pointer_pos[0])
        self.assertEqual(scrollbar.offset, expected_offset)
        self.assertLessEqual(scrollbar.offset, offset_after_reenter)


if __name__ == "__main__":
    unittest.main()
