import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from event_mouse_fixtures import build_mouse_gui_stub
from gui.utility.constants import ArrowPosition, GuiError, InteractiveState, Orientation
from gui.widgets.scrollbar import Scrollbar


class ScrollbarAdditionalPathTests(unittest.TestCase):
    def _build_scrollbar_stub(self) -> Scrollbar:
        scrollbar = Scrollbar.__new__(Scrollbar)
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
        scrollbar._subwidgets_bound = False
        scrollbar._registered = []
        scrollbar._increment_rect = Rect(50, 10, 20, 20)
        scrollbar._decrement_rect = Rect(10, 10, 20, 20)
        scrollbar._inc_degree = 0
        scrollbar._dec_degree = 180
        scrollbar._visible = True
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
                (10, 0, 5, 1),
            )


if __name__ == "__main__":
    unittest.main()
