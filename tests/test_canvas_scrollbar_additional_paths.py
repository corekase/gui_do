import unittest
from collections import deque
from types import SimpleNamespace
from unittest.mock import patch

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from event_mouse_fixtures import build_mouse_gui_stub
from gui.utility.events import ArrowPosition, CanvasEvent, GuiError, InteractiveState, Orientation
from gui.widgets.canvas import Canvas
from gui.widgets.scrollbar import Scrollbar


class _Convertible:
    def convert(self):
        return self


class _CanvasSurface:
    def __init__(self, size):
        self._rect = Rect(0, 0, size[0], size[1])
        self.blit_calls = []

    def convert(self):
        return self

    def get_rect(self):
        return Rect(self._rect)

    def blit(self, src, pos, area=None):
        self.blit_calls.append((src, pos, area))


class CanvasRoiBatch5Tests(unittest.TestCase):
    def _build_canvas_stub(self) -> Canvas:
        canvas = Canvas.__new__(Canvas)
        canvas._disabled = False
        canvas.gui = build_mouse_gui_stub(
            mouse_pos=(5, 5),
            extras={"locking_object": None, "mouse_locked": False},
        )
        canvas.window = None
        canvas.draw_rect = Rect(2, 3, 20, 20)
        canvas.hit_rect = None
        canvas._events = deque([], maxlen=2)
        canvas.dropped_events = 0
        canvas.last_overflow = False
        canvas.on_overflow = None
        canvas._overflow_callback_strict = False
        canvas._overflow_mode = 'drop_oldest'
        canvas.coalesce_motion_events = True
        canvas.queued_event = False
        canvas.CEvent = None
        canvas.surface = SimpleNamespace(blit=lambda *_args, **_kwargs: None)
        canvas.canvas = _CanvasSurface((20, 20))
        canvas.pristine = _Convertible()
        canvas.auto_restore_pristine = False
        return canvas

    def test_constructor_validates_on_activate_callable(self) -> None:
        with self.assertRaises(GuiError):
            Canvas(SimpleNamespace(), "c", Rect(0, 0, 10, 10), on_activate=123)  # type: ignore[arg-type]

    def test_constructor_without_backdrop_draws_frame_and_caches_pristine(self) -> None:
        frame_calls = []
        copy_calls = []
        gui = SimpleNamespace(
            copy_graphic_area=lambda surface, area: copy_calls.append((surface, area)) or _Convertible(),
            set_pristine=lambda *_args, **_kwargs: None,
        )

        class FakeFrame:
            def __init__(self, *_args, **_kwargs):
                self.state = None
                self.surface = None

            def draw(self):
                frame_calls.append(True)

        with patch("gui.widgets.canvas.pygame.surface.Surface", side_effect=lambda size: _CanvasSurface(size)), patch(
            "gui.widgets.canvas.Frame", FakeFrame
        ):
            canvas = Canvas(gui, "canvas", Rect(0, 0, 30, 20), backdrop=None)

        self.assertEqual(len(frame_calls), 1)
        self.assertEqual(len(copy_calls), 1)
        self.assertIsNotNone(canvas.pristine)

    def test_constructor_with_backdrop_uses_set_pristine(self) -> None:
        pristine_calls = []
        gui = SimpleNamespace(
            copy_graphic_area=lambda *_args, **_kwargs: _Convertible(),
            set_pristine=lambda image, obj: pristine_calls.append((image, obj)),
        )

        with patch("gui.widgets.canvas.pygame.surface.Surface", side_effect=lambda size: _CanvasSurface(size)):
            canvas = Canvas(gui, "canvas", Rect(0, 0, 16, 10), backdrop="bg.png")

        self.assertEqual(len(pristine_calls), 1)
        self.assertEqual(pristine_calls[0][0], "bg.png")
        self.assertIs(pristine_calls[0][1], canvas)

    def test_queue_limit_and_read_event_paths(self) -> None:
        canvas = self._build_canvas_stub()

        self.assertEqual(canvas.get_event_queue_limit(), 2)
        canvas._events = deque([1, 2])
        self.assertEqual(canvas.get_event_queue_limit(), 0)

        canvas._events = deque([], maxlen=2)
        self.assertIsNone(canvas.read_event())
        self.assertFalse(canvas.queued_event)
        self.assertIsNone(canvas.CEvent)

        evt1 = SimpleNamespace(type=CanvasEvent.MouseMotion)
        evt2 = SimpleNamespace(type=CanvasEvent.MouseWheel)
        canvas._events = deque([evt1, evt2], maxlen=2)
        self.assertIs(canvas.read_event(), evt1)
        self.assertTrue(canvas.queued_event)
        self.assertIs(canvas.CEvent, evt2)

    def test_set_queue_limit_and_validation_guards(self) -> None:
        canvas = self._build_canvas_stub()
        canvas._events = deque([SimpleNamespace(type=CanvasEvent.MouseButtonDown)], maxlen=2)

        canvas.set_event_queue_limit(4)
        self.assertEqual(canvas.get_event_queue_limit(), 4)
        self.assertTrue(canvas.queued_event)
        self.assertIsNotNone(canvas.CEvent)

        with self.assertRaises(GuiError):
            canvas.set_event_queue_limit("bad")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            canvas.set_event_queue_limit(0)

        # No-op branch when maxlen already matches.
        existing = canvas._events
        canvas._configure_max_queued_events(4)
        self.assertIs(canvas._events, existing)

    def test_motion_and_overflow_callback_validation(self) -> None:
        canvas = self._build_canvas_stub()

        canvas.set_motion_coalescing(False)
        self.assertFalse(canvas.coalesce_motion_events)
        with self.assertRaises(GuiError):
            canvas.set_motion_coalescing(1)  # type: ignore[arg-type]

        canvas.set_overflow_handler(None)
        canvas.set_overflow_handler(lambda _dropped, _total: None)
        canvas.set_overflow_handler(lambda _dropped, _total: None, strict=True)
        with self.assertRaises(GuiError):
            canvas.set_overflow_handler(1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            canvas.set_overflow_handler(lambda _dropped, _total: None, strict=1)  # type: ignore[arg-type]

    def test_overflow_mode_and_stats_reset(self) -> None:
        canvas = self._build_canvas_stub()

        self.assertEqual(canvas.get_overflow_mode(), 'drop_oldest')
        canvas.set_overflow_mode('reject_new')
        self.assertEqual(canvas.get_overflow_mode(), 'reject_new')

        stats = canvas.get_event_queue_stats()
        self.assertEqual(stats['queued'], 0)
        self.assertEqual(stats['limit'], 2)
        self.assertEqual(stats['dropped_events'], 0)
        self.assertFalse(stats['last_overflow'])
        self.assertEqual(stats['overflow_mode'], 'reject_new')

        canvas._events.append(SimpleNamespace(type=CanvasEvent.MouseMotion))
        canvas.dropped_events = 3
        canvas.last_overflow = True
        canvas.queued_event = True
        canvas.CEvent = canvas._events[0]
        canvas.reset_event_queue_stats(clear_queue=True)
        self.assertEqual(canvas.dropped_events, 0)
        self.assertFalse(canvas.last_overflow)
        self.assertEqual(len(canvas._events), 0)
        self.assertFalse(canvas.queued_event)
        self.assertIsNone(canvas.CEvent)

        with self.assertRaises(GuiError):
            canvas.set_overflow_mode('bad-mode')
        with self.assertRaises(GuiError):
            canvas.reset_event_queue_stats(clear_queue=1)  # type: ignore[arg-type]

    def test_handle_event_non_collide_but_locked_owner_still_queues(self) -> None:
        canvas = self._build_canvas_stub()
        canvas.gui.locking_object = canvas
        canvas.gui.mouse_locked = True
        canvas.get_collide = lambda _window=None: False

        event = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        handled = canvas.handle_event(event, None)

        self.assertTrue(handled)
        self.assertEqual(len(canvas._events), 1)
        self.assertEqual(canvas._events[0].type, CanvasEvent.MouseButtonDown)

    def test_overflow_callback_exception_is_swallowed(self) -> None:
        canvas = self._build_canvas_stub()
        canvas.get_collide = lambda _window=None: True
        canvas.coalesce_motion_events = False
        canvas._events = deque([], maxlen=1)

        def _boom(_dropped: int, _total: int) -> None:
            raise RuntimeError("overflow callback boom")

        canvas.on_overflow = _boom

        first = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        second = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})

        self.assertTrue(canvas.handle_event(first, None))
        self.assertTrue(canvas.handle_event(second, None))
        self.assertEqual(canvas.dropped_events, 1)
        self.assertTrue(canvas.last_overflow)
        self.assertEqual(len(canvas._events), 1)

    def test_overflow_callback_exception_strict_mode_raises(self) -> None:
        canvas = self._build_canvas_stub()
        canvas.get_collide = lambda _window=None: True
        canvas.coalesce_motion_events = False
        canvas._events = deque([], maxlen=1)

        def _boom(_dropped: int, _total: int) -> None:
            raise RuntimeError('overflow callback boom')

        canvas.set_overflow_handler(_boom, strict=True)
        first = pygame.event.Event(MOUSEBUTTONDOWN, {'button': 1})
        second = pygame.event.Event(MOUSEBUTTONDOWN, {'button': 1})

        self.assertTrue(canvas.handle_event(first, None))
        with self.assertRaises(GuiError):
            canvas.handle_event(second, None)

    def test_reject_new_overflow_mode_preserves_existing_queue(self) -> None:
        canvas = self._build_canvas_stub()
        canvas.get_collide = lambda _window=None: True
        canvas.coalesce_motion_events = False
        canvas.set_overflow_mode('reject_new')
        canvas._events = deque([], maxlen=1)

        first = pygame.event.Event(MOUSEBUTTONDOWN, {'button': 1})
        second = pygame.event.Event(MOUSEBUTTONUP, {'button': 1})

        self.assertTrue(canvas.handle_event(first, None))
        queued_before = canvas._events[0]
        self.assertTrue(canvas.handle_event(second, None))
        self.assertEqual(len(canvas._events), 1)
        self.assertIs(canvas._events[0], queued_before)
        self.assertEqual(canvas.dropped_events, 1)

    def test_draw_auto_restore_branch_and_focus_else(self) -> None:
        canvas = self._build_canvas_stub()
        restore_calls = []
        canvas.auto_restore_pristine = True
        canvas.restore_pristine = lambda area=None: restore_calls.append(area)

        canvas.draw()
        self.assertEqual(restore_calls, [None])

        canvas.gui.set_mouse_pos((999, 999))
        self.assertFalse(canvas.focused())

    def test_disabled_draw_dims_live_canvas_contents_not_cached_bitmap(self) -> None:
        canvas = self._build_canvas_stub()
        blit_calls = []
        overlay_seen_sources = []

        canvas.surface = SimpleNamespace(blit=lambda src, dst: blit_calls.append((src, dst)))
        canvas._disabled = True

        def _fake_overlay():
            overlay_seen_sources.append(blit_calls[-1][0] if blit_calls else None)

        canvas._blit_disabled_overlay = _fake_overlay

        canvas.draw()
        self.assertEqual(len(blit_calls), 1)
        self.assertIs(blit_calls[0][0], canvas.canvas)
        self.assertEqual(blit_calls[0][1], canvas.draw_rect)
        self.assertEqual(overlay_seen_sources, [canvas.canvas])

        # A subsequent draw must still dim whatever canvas surface is current.
        updated_canvas_surface = _CanvasSurface((20, 20))
        canvas.canvas = updated_canvas_surface
        blit_calls.clear()
        overlay_seen_sources.clear()

        canvas.draw()
        self.assertEqual(len(blit_calls), 1)
        self.assertIs(blit_calls[0][0], updated_canvas_surface)
        self.assertEqual(blit_calls[0][1], canvas.draw_rect)
        self.assertEqual(overlay_seen_sources, [updated_canvas_surface])


class ScrollbarRoiBatch5Tests(unittest.TestCase):
    def _fake_frame_init(self, instance, gui, sid, rect):
        instance.gui = gui
        instance.id = sid
        instance.draw_rect = Rect(rect)
        instance.hit_rect = None
        instance.surface = SimpleNamespace(blit=lambda *_args, **_kwargs: None)

    def test_constructor_covers_skip_near_far_split_and_orientation_branches(self) -> None:
        gui = SimpleNamespace()

        with patch(
            "gui.widgets.scrollbar.Frame.__init__",
            autospec=True,
            side_effect=lambda s, g, i, r: self._fake_frame_init(s, g, i, r),
        ):
            skip = Scrollbar(gui, "skip", Rect(0, 0, 80, 20), Orientation.Horizontal, ArrowPosition.Skip, (20, 0, 10, 1))
            self.assertIsNone(skip._increment_rect)
            self.assertIsNone(skip._decrement_rect)

            near_h = Scrollbar(gui, "near_h", Rect(0, 0, 80, 20), Orientation.Horizontal, ArrowPosition.Near, (20, 0, 10, 1))
            self.assertEqual(near_h._inc_degree, 0)
            self.assertEqual(near_h._dec_degree, 180)

            near_v = Scrollbar(gui, "near_v", Rect(0, 0, 20, 80), Orientation.Vertical, ArrowPosition.Near, (20, 0, 10, 1))
            self.assertEqual(near_v._inc_degree, 270)
            self.assertEqual(near_v._dec_degree, 90)

            far_h = Scrollbar(gui, "far_h", Rect(0, 0, 80, 20), Orientation.Horizontal, ArrowPosition.Far, (20, 0, 10, 1))
            self.assertIsNotNone(far_h._increment_rect)
            self.assertIsNotNone(far_h._decrement_rect)

            split_v = Scrollbar(gui, "split_v", Rect(0, 0, 20, 80), Orientation.Vertical, ArrowPosition.Split, (20, 0, 10, 1))
            self.assertIsNotNone(split_v._increment_rect)
            self.assertIsNotNone(split_v._decrement_rect)

    def test_leave_calls_reset_and_buttonup_non_left_falls_through(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._dragging = True
        scrollbar._last_mouse_pos = 3
        scrollbar.state = InteractiveState.Hover
        scrollbar._hit = False
        lock_calls = []
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(0, 0),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
        )

        Scrollbar.leave(scrollbar)
        self.assertFalse(scrollbar._dragging)
        self.assertEqual(scrollbar.state, InteractiveState.Idle)

        scrollbar._dragging = True
        evt = pygame.event.Event(MOUSEBUTTONUP, {"button": 3})
        self.assertFalse(scrollbar.handle_event(evt, None))
        self.assertEqual(lock_calls, [(None, None)])

    def test_vertical_drag_path_and_graphical_range_vertical(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._hit = False
        scrollbar._dragging = True
        scrollbar._horizontal = Orientation.Vertical
        scrollbar._graphic_rect = Rect(10, 10, 20, 100)
        scrollbar._total_range = 100
        scrollbar._bar_size = 20
        scrollbar._start_pos = 5
        scrollbar._last_mouse_pos = None
        scrollbar.gui = build_mouse_gui_stub(mouse_pos=(20, 40))

        motion = pygame.event.Event(MOUSEMOTION, {})
        self.assertFalse(scrollbar.handle_event(motion, None))
        self.assertEqual(scrollbar._last_mouse_pos, 30)
        self.assertEqual(Scrollbar._graphical_range(scrollbar), 100)

    def test_disabled_scrollbar_does_not_process_input(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = True
        scrollbar._hit = True
        scrollbar._dragging = True
        scrollbar._last_mouse_pos = 7
        scrollbar._horizontal = Orientation.Horizontal
        scrollbar._graphic_rect = Rect(10, 10, 50, 10)
        scrollbar._total_range = 100
        scrollbar._bar_size = 20
        scrollbar._start_pos = 5
        scrollbar.gui = build_mouse_gui_stub(mouse_pos=(20, 10))

        handled = scrollbar.handle_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}), None)

        self.assertFalse(handled)
        self.assertTrue(scrollbar._hit)
        self.assertTrue(scrollbar._dragging)
        self.assertEqual(scrollbar._last_mouse_pos, 7)

    def test_drag_cancels_when_screen_scrollbar_enters_window_overlay(self) -> None:
        lock_calls = []
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._hit = False
        scrollbar._dragging = True
        scrollbar._last_mouse_pos = 3
        scrollbar._horizontal = Orientation.Horizontal
        scrollbar._graphic_rect = Rect(0, 0, 100, 12)
        scrollbar._total_range = 100
        scrollbar._bar_size = 20
        scrollbar._start_pos = 5
        scrollbar.state = InteractiveState.Hover
        overlay = SimpleNamespace(visible=True, get_window_rect=lambda: Rect(10, 0, 60, 30))
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(20, 6),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
            extras={"windows": [overlay]},
        )

        self.assertTrue(scrollbar.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        self.assertFalse(scrollbar._dragging)
        self.assertEqual(scrollbar.state, InteractiveState.Idle)
        self.assertEqual(lock_calls, [(None, None)])

    def test_drag_cancels_when_window_scrollbar_enters_higher_window_overlay(self) -> None:
        lock_calls = []
        owner_window = SimpleNamespace(visible=True, get_window_rect=lambda: Rect(0, 0, 200, 80))
        overlay_window = SimpleNamespace(visible=True, get_window_rect=lambda: Rect(30, 0, 80, 80))
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._disabled = False
        scrollbar._hit = False
        scrollbar._dragging = True
        scrollbar._last_mouse_pos = 4
        scrollbar._horizontal = Orientation.Horizontal
        scrollbar._graphic_rect = Rect(0, 0, 100, 12)
        scrollbar._total_range = 100
        scrollbar._bar_size = 20
        scrollbar._start_pos = 5
        scrollbar.state = InteractiveState.Hover
        scrollbar.gui = build_mouse_gui_stub(
            mouse_pos=(40, 6),
            set_lock_area=lambda value, area=None: lock_calls.append((value, area)),
            extras={"windows": [owner_window, overlay_window]},
        )

        self.assertTrue(scrollbar.handle_event(pygame.event.Event(MOUSEMOTION, {}), owner_window))
        self.assertFalse(scrollbar._dragging)
        self.assertEqual(scrollbar.state, InteractiveState.Idle)
        self.assertEqual(lock_calls, [(None, None)])


if __name__ == "__main__":
    unittest.main()
