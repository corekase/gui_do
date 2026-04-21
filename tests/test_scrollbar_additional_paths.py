import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL

from event_mouse_fixtures import build_mouse_gui_stub
from gui.utility.events import ArrowPosition, GuiError, InteractiveState, Orientation
from gui.widgets.scrollbar import Scrollbar


class ScrollbarAdditionalPathTests(unittest.TestCase):
    def _build_scrollbar_stub(self) -> Scrollbar:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar.id = "sb"
        scrollbar.state = InteractiveState.Idle
        scrollbar._style = ArrowPosition.Split
        scrollbar._horizontal = Orientation.Horizontal
        scrollbar._graphic_rect = Rect(10, 10, 100, 20)
        scrollbar._total_range = 100
        scrollbar._bar_size = 20
        scrollbar._start_pos = 10
        scrollbar._inc_size = 5
        scrollbar._hit = False
        scrollbar._dragging = False
        scrollbar._last_mouse_pos = None
        scrollbar._drag_left_widget_bounds = False
        scrollbar._last_in_bounds_screen_pos = None
        scrollbar._subwidgets_bound = False
        scrollbar._registered = []
        scrollbar.draw_rect = Rect(0, 0, 200, 40)
        scrollbar.hit_rect = None
        scrollbar._increment_rect = Rect(50, 10, 20, 20)
        scrollbar._decrement_rect = Rect(10, 10, 20, 20)
        scrollbar._inc_degree = 0
        scrollbar._dec_degree = 180
        scrollbar._visible = True
        scrollbar._wheel_positive_to_max = False
        return scrollbar

    def test_visible_setter_validates_and_propagates(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        child1 = SimpleNamespace(visible=True)
        child2 = SimpleNamespace(visible=True)
        scrollbar._registered = [child1, child2]

        scrollbar.visible = False
        self.assertFalse(scrollbar.visible)
        self.assertFalse(child1.visible)
        self.assertFalse(child2.visible)

        with self.assertRaises(GuiError):
            scrollbar.visible = 1  # type: ignore[assignment]

    def test_disabled_setter_propagates_to_arrows_and_resets_state(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        arrow1 = SimpleNamespace(disabled=False)
        arrow2 = SimpleNamespace(disabled=False)
        scrollbar._registered = [arrow1, arrow2]
        scrollbar._dragging = True
        scrollbar._last_mouse_pos = 7
        scrollbar.state = InteractiveState.Hover
        lock_calls = []
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(0, 0),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
        )

        scrollbar.disabled = True

        self.assertTrue(scrollbar.disabled)
        self.assertTrue(arrow1.disabled)
        self.assertTrue(arrow2.disabled)
        self.assertFalse(scrollbar._dragging)
        self.assertIsNone(scrollbar._last_mouse_pos)
        self.assertEqual(scrollbar.state, InteractiveState.Idle)
        self.assertEqual(lock_calls, [(None, None)])

        scrollbar.disabled = False
        self.assertFalse(scrollbar.disabled)
        self.assertFalse(arrow1.disabled)
        self.assertFalse(arrow2.disabled)

    def test_set_validates_ranges(self) -> None:
        scrollbar = self._build_scrollbar_stub()

        with self.assertRaises(GuiError):
            scrollbar.set(0, 0, 1, 1)
        with self.assertRaises(GuiError):
            scrollbar.set(10, 0, 11, 1)
        with self.assertRaises(GuiError):
            scrollbar.set(10, -1, 5, 1)
        with self.assertRaises(GuiError):
            scrollbar.set(10, 0, 5, 0)

        scrollbar.set(10, 3, 5, 2)
        self.assertEqual(scrollbar.start_pos, 3)

    def test_handle_event_short_circuits_hit_and_non_mouse_events(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        scrollbar._hit = True
        scrollbar.gui = SimpleNamespace()

        self.assertTrue(scrollbar.handle_event(pygame.event.Event(KEYDOWN, {}), None))
        self.assertFalse(scrollbar._hit)

        self.assertFalse(scrollbar.handle_event(pygame.event.Event(KEYDOWN, {}), None))

    def test_handle_event_mouse_down_starts_drag_and_locks(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        lock_calls = []
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(25, 15),
            set_lock_area=lambda widget, area=None: lock_calls.append((widget, area)),
        )

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})

        self.assertFalse(scrollbar.handle_event(down, None))
        self.assertTrue(scrollbar._dragging)
        self.assertEqual(scrollbar.state, InteractiveState.Hover)
        self.assertEqual(len(lock_calls), 1)
        self.assertIs(lock_calls[0][0], scrollbar)

    def test_handle_event_drag_motion_clamps_and_tracks(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        scrollbar._dragging = True
        scrollbar.gui = build_mouse_gui_stub(mouse_pos=(0, 0))

        motion = pygame.event.Event(MOUSEMOTION, {})

        # First motion computes point < 0 and clamps to zero.
        self.assertTrue(scrollbar.handle_event(motion, None))
        self.assertEqual(scrollbar._start_pos, 0)
        self.assertEqual(scrollbar._last_mouse_pos, 0)

        # Extreme right motion clamps to max start.
        scrollbar.gui.set_mouse_pos((1000, 0))
        self.assertTrue(scrollbar.handle_event(motion, None))
        self.assertEqual(scrollbar._start_pos, 80)
        self.assertEqual(scrollbar._last_mouse_pos, 80)

        # Mid-range motion updates by delta.
        scrollbar._start_pos = 10
        scrollbar._last_mouse_pos = 20
        scrollbar.gui.set_mouse_pos((40, 0))
        self.assertTrue(scrollbar.handle_event(motion, None))
        self.assertEqual(scrollbar._start_pos, 20)
        self.assertEqual(scrollbar._last_mouse_pos, 30)

        # First mid-range event with no last mouse pos sets tracker and returns False.
        scrollbar._last_mouse_pos = None
        scrollbar._start_pos = 10
        scrollbar.gui.set_mouse_pos((30, 0))
        self.assertFalse(scrollbar.handle_event(motion, None))
        self.assertEqual(scrollbar._last_mouse_pos, 20)

    def test_handle_event_mouse_up_resets_drag(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        lock_calls = []
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(0, 0),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
        )
        scrollbar._dragging = True
        scrollbar._last_mouse_pos = 5
        scrollbar._hit = False
        scrollbar.state = InteractiveState.Hover

        up = pygame.event.Event(MOUSEBUTTONUP, {"button": 1})

        self.assertTrue(scrollbar.handle_event(up, None))
        self.assertFalse(scrollbar._dragging)
        self.assertIsNone(scrollbar._last_mouse_pos)
        self.assertFalse(scrollbar._hit)
        self.assertEqual(scrollbar.state, InteractiveState.Idle)
        self.assertEqual(lock_calls, [(None, None)])

    def test_release_after_leaving_bounds_and_reentering_preserves_release_position(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        lock_calls = []
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(25, 15),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
        )

        self.assertFalse(scrollbar.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None))

        scrollbar.gui.set_mouse_pos((scrollbar.draw_rect.right + 60, scrollbar.draw_rect.centery))
        self.assertTrue(scrollbar.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))

        release_pos = (scrollbar.draw_rect.centerx, scrollbar.draw_rect.centery)
        self.assertTrue(scrollbar.handle_event(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": release_pos}), None))
        self.assertEqual(scrollbar.gui._get_mouse_pos(), release_pos)

    def test_release_uses_last_in_bounds_motion_when_release_pos_is_outside(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        lock_calls = []
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(25, 15),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
        )

        self.assertFalse(scrollbar.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (25, 15)}), None))

        inside_pos = (scrollbar.draw_rect.centerx, scrollbar.draw_rect.centery)
        scrollbar.gui.set_mouse_pos(inside_pos)
        self.assertFalse(scrollbar.handle_event(pygame.event.Event(MOUSEMOTION, {"pos": inside_pos}), None))

        outside_pos = (scrollbar.draw_rect.right + 80, scrollbar.draw_rect.centery)
        scrollbar.gui.set_mouse_pos(outside_pos)
        self.assertTrue(scrollbar.handle_event(pygame.event.Event(MOUSEMOTION, {"pos": outside_pos}), None))

        release_outside = (scrollbar.draw_rect.right + 100, scrollbar.draw_rect.centery)
        self.assertTrue(scrollbar.handle_event(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": release_outside}), None))
        self.assertEqual(scrollbar.gui._get_mouse_pos(), inside_pos)

    def test_mousewheel_on_hover_decrements_towards_zero_by_default(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        scrollbar._start_pos = 10
        scrollbar._inc_size = 2
        scrollbar.draw_rect = Rect(0, 0, 200, 40)
        scrollbar.gui = build_mouse_gui_stub(mouse_pos=scrollbar.draw_rect.center)

        handled = scrollbar.handle_event(pygame.event.Event(MOUSEWHEEL, {"y": 1}), None)

        self.assertTrue(handled)
        self.assertEqual(scrollbar._start_pos, 8)
        self.assertEqual(scrollbar.state, InteractiveState.Hover)

    def test_mousewheel_on_hover_increments_towards_max_when_enabled(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        scrollbar._start_pos = 10
        scrollbar._inc_size = 2
        scrollbar._wheel_positive_to_max = True
        scrollbar.draw_rect = Rect(0, 0, 200, 40)
        scrollbar.gui = build_mouse_gui_stub(mouse_pos=scrollbar.draw_rect.center)

        handled = scrollbar.handle_event(pygame.event.Event(MOUSEWHEEL, {"y": 1}), None)

        self.assertTrue(handled)
        self.assertEqual(scrollbar._start_pos, 12)
        self.assertEqual(scrollbar.state, InteractiveState.Hover)

    def test_mousewheel_ignores_events_when_not_hovered(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        scrollbar._start_pos = 10
        scrollbar.draw_rect = Rect(0, 0, 200, 40)
        scrollbar.gui = build_mouse_gui_stub(mouse_pos=(999, 999))

        handled = scrollbar.handle_event(pygame.event.Event(MOUSEWHEEL, {"y": 1}), None)

        self.assertFalse(handled)
        self.assertEqual(scrollbar._start_pos, 10)

    def test_on_added_to_gui_validates_geometry_and_binds_arrows(self) -> None:
        scrollbar = self._build_scrollbar_stub()
        scrollbar._increment_rect = None
        scrollbar.gui = SimpleNamespace()

        with self.assertRaises(GuiError):
            scrollbar._on_added_to_gui()

        scrollbar._increment_rect = Rect(50, 10, 20, 20)
        scrollbar._decrement_rect = Rect(10, 10, 20, 20)
        scrollbar._inc_degree = None

        with self.assertRaises(GuiError):
            scrollbar._on_added_to_gui()

        created = []

        def build_arrow(aid, arect, degree, callback):
            arrow = SimpleNamespace(id=aid, rect=arect, degree=degree, callback=callback)
            created.append(arrow)
            return arrow

        scrollbar._inc_degree = 0
        scrollbar._dec_degree = 180
        scrollbar.gui = SimpleNamespace(arrow_box=build_arrow, widgets=[], windows=[])

        scrollbar._on_added_to_gui()

        self.assertTrue(scrollbar._subwidgets_bound)
        self.assertEqual(len(scrollbar._registered), 2)
        self.assertEqual(created[0].id, "sb.increment")
        self.assertEqual(created[1].id, "sb.decrement")

        # Re-entry should be a no-op when already bound.
        before = list(scrollbar._registered)
        scrollbar._on_added_to_gui()
        self.assertEqual(scrollbar._registered, before)

    def test_on_added_to_gui_rolls_back_created_arrows_on_failure(self) -> None:
        scrollbar = self._build_scrollbar_stub()

        window = SimpleNamespace(widgets=[])
        widgets = []

        def build_arrow(aid, arect, degree, callback):
            arrow = SimpleNamespace(id=aid, rect=arect, degree=degree, callback=callback)
            widgets.append(arrow)
            window.widgets.append(arrow)
            return arrow

        class _FailingRegistry(list):
            def extend(self, values):
                raise RuntimeError("boom")

        scrollbar._registered = _FailingRegistry()

        scrollbar.gui = SimpleNamespace(arrow_box=build_arrow, widgets=widgets, windows=[window])

        with self.assertRaises(RuntimeError):
            scrollbar._on_added_to_gui()

        self.assertEqual(len(widgets), 0)
        self.assertEqual(len(window.widgets), 0)

    def test_constructor_rejects_unknown_style(self) -> None:
        with self.assertRaises(GuiError):
            Scrollbar(
                SimpleNamespace(),
                "sb",
                Rect(0, 0, 100, 20),
                Orientation.Horizontal,
                "bad-style",  # type: ignore[arg-type]
                10,
                0,
                5,
                1,
            )

    def test_constructor_validates_wheel_positive_to_max_type(self) -> None:
        with self.assertRaises(GuiError):
            Scrollbar(
                SimpleNamespace(),
                "sb",
                Rect(0, 0, 100, 20),
                Orientation.Horizontal,
                ArrowPosition.Skip,
                10,
                0,
                5,
                1,
                wheel_positive_to_max=1,  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
