import unittest

import pygame
from pygame import Rect, SRCALPHA
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from event_mouse_fixtures import build_mouse_gui_stub
from gui.utility.events import GuiError, InteractiveState, Orientation
from gui.widgets.slider import Slider


class _FakeGraphicsFactory:
    def centre(self, bigger: int, smaller: int) -> int:
        return int((bigger / 2) - (smaller / 2))

    def build_disabled_bitmap(self, idle_bitmap):
        return idle_bitmap.copy()

    def draw_radio_bitmap(self, size: int, _col1, _col2):
        return pygame.Surface((size, size), SRCALPHA)


class SliderWidgetContractTests(unittest.TestCase):
    def _build_slider(
        self,
        *,
        orientation: Orientation = Orientation.Horizontal,
        integer_type: bool = False,
        total_range: int = 10,
        notch_interval_percent: float = 5.0,
        position: float = 0.0,
    ) -> Slider:
        lock_calls = []
        gui = build_mouse_gui_stub(
            mouse_pos=(20, 10),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
            extras={"graphics_factory": _FakeGraphicsFactory()},
        )
        slider = Slider(gui, "slider", Rect(0, 0, 120, 20), orientation, total_range, position, integer_type, notch_interval_percent)
        slider._lock_calls = lock_calls  # type: ignore[attr-defined]
        return slider

    def test_value_snaps_to_integer_when_enabled(self) -> None:
        slider = self._build_slider(integer_type=True)

        slider.value = 3.6

        self.assertEqual(slider.value, 4.0)

    def test_value_preserves_fraction_when_integer_snap_disabled(self) -> None:
        slider = self._build_slider(integer_type=False)

        slider.value = 3.6

        self.assertAlmostEqual(slider.value, 3.6, places=2)

    def test_drag_motion_updates_value_and_clamps(self) -> None:
        slider = self._build_slider()

        start = slider._handle_area().center
        slider.gui.set_mouse_pos(start)
        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None))

        slider.gui.set_mouse_pos((slider._graphic_rect.right + 200, start[1]))
        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        self.assertEqual(slider.value, 10.0)

        slider.gui.set_mouse_pos((slider._graphic_rect.left - 200, start[1]))
        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        self.assertEqual(slider.value, 0.0)

        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEBUTTONUP, {"button": 1}), None))
        self.assertFalse(slider._dragging)

        lock_calls = slider._lock_calls  # type: ignore[attr-defined]
        self.assertTrue(any(call[0] is slider for call in lock_calls))
        self.assertIn((None, None), lock_calls)

    def test_horizontal_drag_locks_to_anchor_adjusted_travel_corridor(self) -> None:
        slider = self._build_slider(orientation=Orientation.Horizontal, total_range=100, position=20.0)
        handle = slider._handle_area()
        down_point = (handle.x + 3, handle.centery)
        slider.gui.set_mouse_pos(down_point)

        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None))

        lock_calls = slider._lock_calls  # type: ignore[attr-defined]
        lock_widget, lock_rect = lock_calls[0]
        self.assertIs(lock_widget, slider)
        self.assertEqual(lock_rect.x, slider._graphic_rect.x + 3)
        self.assertEqual(lock_rect.y, down_point[1])
        self.assertEqual(lock_rect.width, slider._graphic_rect.width + 1)
        self.assertEqual(lock_rect.height, 1)

    def test_vertical_drag_locks_to_anchor_adjusted_travel_corridor(self) -> None:
        slider = self._build_slider(orientation=Orientation.Vertical, total_range=100, position=20.0)
        handle = slider._handle_area()
        down_point = (handle.centerx, handle.y + 4)
        slider.gui.set_mouse_pos(down_point)

        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None))

        lock_calls = slider._lock_calls  # type: ignore[attr-defined]
        lock_widget, lock_rect = lock_calls[0]
        self.assertIs(lock_widget, slider)
        self.assertEqual(lock_rect.x, down_point[0])
        self.assertEqual(lock_rect.y, slider._graphic_rect.y + 4)
        self.assertEqual(lock_rect.width, 1)
        self.assertEqual(lock_rect.height, slider._graphic_rect.height + 1)

    def test_disabled_state_resets_dragging_state(self) -> None:
        slider = self._build_slider()
        slider._dragging = True
        slider.state = InteractiveState.Armed

        slider.disabled = True

        self.assertEqual(slider.state, InteractiveState.Disabled)
        self.assertFalse(slider._dragging)

    def test_graphical_range_respects_orientation(self) -> None:
        slider = Slider.__new__(Slider)
        slider._disabled = False
        slider._graphic_rect = Rect(0, 0, 40, 10)

        slider._horizontal = Orientation.Horizontal
        self.assertEqual(Slider._graphical_range(slider), 40)

        slider._horizontal = Orientation.Vertical
        self.assertEqual(Slider._graphical_range(slider), 10)

    def test_drag_preserves_initial_mouse_to_handle_offset(self) -> None:
        slider = self._build_slider(total_range=100, position=20.0)
        handle = slider._handle_area()
        # Click near the right side of the handle, not at the origin.
        down_point = (handle.right - 1, handle.centery)
        slider.gui.set_mouse_pos(down_point)
        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None))

        # No mouse movement should keep logical value unchanged.
        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        self.assertAlmostEqual(slider.value, 20.0, delta=1.0)

        # Moving by +7 px should track by that delta only.
        slider.gui.set_mouse_pos((down_point[0] + 7, down_point[1]))
        self.assertTrue(slider.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        expected = slider.pixel_to_total(slider.total_to_pixel(20.0, slider._total_range) + 7, slider._total_range)
        self.assertAlmostEqual(slider.value, expected, delta=1.0)

    def test_notch_points_default_to_every_five_percent(self) -> None:
        slider = self._build_slider(total_range=200, notch_interval_percent=5.0)

        points = slider._notch_points()

        self.assertEqual(points[0], 0.0)
        self.assertEqual(points[-1], 200.0)
        self.assertIn(10.0, points)
        self.assertIn(190.0, points)

    def test_integer_slider_notches_align_to_integer_positions(self) -> None:
        slider = self._build_slider(total_range=12, integer_type=True, notch_interval_percent=50.0)

        points = slider._notch_points()

        self.assertEqual(points, [float(index) for index in range(13)])

    def test_integer_notches_span_full_handle_reachable_range(self) -> None:
        slider = self._build_slider(total_range=12, integer_type=True)

        points = slider._notch_points()
        start_pixel = slider.total_to_pixel(points[0], slider._total_range)
        end_pixel = slider.total_to_pixel(points[-1], slider._total_range)

        self.assertEqual(points[0], 0.0)
        self.assertEqual(points[-1], 12.0)
        self.assertEqual(start_pixel, 0)
        self.assertEqual(end_pixel, slider._graphical_range())

    def test_horizontal_handle_touches_overall_rect_borders_at_range_ends(self) -> None:
        slider = self._build_slider(orientation=Orientation.Horizontal, total_range=100)

        slider.value = 0.0
        min_handle = slider._handle_area()
        slider.value = 100.0
        max_handle = slider._handle_area()

        self.assertEqual(min_handle.left, slider.draw_rect.left)
        self.assertEqual(max_handle.right, slider.draw_rect.right)

    def test_vertical_handle_touches_overall_rect_borders_at_range_ends(self) -> None:
        slider = self._build_slider(orientation=Orientation.Vertical, total_range=100)

        slider.value = 0.0
        min_handle = slider._handle_area()
        slider.value = 100.0
        max_handle = slider._handle_area()

        self.assertEqual(min_handle.top, slider.draw_rect.top)
        self.assertEqual(max_handle.bottom, slider.draw_rect.bottom)

    def test_handle_graphical_position_matches_expected_float_output(self) -> None:
        slider = self._build_slider(orientation=Orientation.Horizontal, total_range=100, integer_type=False)

        slider.value = 37.5
        handle = slider._handle_area()
        expected_offset = slider.total_to_pixel(37.5, slider._total_range)

        self.assertEqual(handle.x, slider._graphic_rect.x + expected_offset)

    def test_handle_graphical_position_matches_expected_integer_output(self) -> None:
        slider = self._build_slider(orientation=Orientation.Horizontal, total_range=100, integer_type=True)

        slider.value = 37.6
        handle = slider._handle_area()
        snapped_value = 38.0
        expected_offset = slider.total_to_pixel(snapped_value, slider._total_range)

        self.assertEqual(slider.value, snapped_value)
        self.assertEqual(handle.x, slider._graphic_rect.x + expected_offset)

    def test_vertical_handle_graphical_position_matches_expected_float_output(self) -> None:
        slider = self._build_slider(orientation=Orientation.Vertical, total_range=80, integer_type=False)

        slider.value = 26.25
        handle = slider._handle_area()
        expected_offset = slider.total_to_pixel(26.25, slider._total_range)

        self.assertEqual(handle.y, slider._graphic_rect.y + expected_offset)

    def test_vertical_handle_graphical_position_matches_expected_integer_output(self) -> None:
        slider = self._build_slider(orientation=Orientation.Vertical, total_range=80, integer_type=True)

        slider.value = 26.51
        handle = slider._handle_area()
        snapped_value = 27.0
        expected_offset = slider.total_to_pixel(snapped_value, slider._total_range)

        self.assertEqual(slider.value, snapped_value)
        self.assertEqual(handle.y, slider._graphic_rect.y + expected_offset)

    def test_disabled_draw_uses_dimmed_bar_and_handle(self) -> None:
        slider = self._build_slider()

        class _SurfaceRecorder:
            def __init__(self) -> None:
                self.blit_calls = []

            def blit(self, bitmap, position):
                self.blit_calls.append((bitmap, position))

        recorder = _SurfaceRecorder()
        slider.surface = recorder
        slider._disabled_track_bitmap = object()
        slider._disabled_handle = object()

        slider.disabled = True
        slider.draw()

        self.assertEqual(len(recorder.blit_calls), 2)
        self.assertIs(recorder.blit_calls[0][0], slider._disabled_track_bitmap)
        self.assertIs(recorder.blit_calls[1][0], slider._disabled_handle)

    def test_constructor_validates_notch_interval_percent(self) -> None:
        with self.assertRaises(GuiError):
            self._build_slider(notch_interval_percent=0.0)
        with self.assertRaises(GuiError):
            self._build_slider(notch_interval_percent=101.0)

    def test_handle_size_is_reduced_by_twenty_percent(self) -> None:
        slider = self._build_slider()

        self.assertEqual(slider._handle_size, 12)


if __name__ == "__main__":
    unittest.main()
