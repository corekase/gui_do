import unittest
from collections import deque
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEMOTION

from gui.utility.events import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input.input_emitter import InputEventEmitter
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from gui.utility.scheduler import Scheduler, Task
from gui.widgets.canvas import Canvas, CanvasEvent


class SimpleGuiEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class EventDispatcherGuiStub:
    def __init__(self) -> None:
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.locking_object = None
        self.task_panel = None
        self.active_window = None
        self.windows = []
        self.widgets = []
        self.mouse_locked = False
        self.mouse_pos = (0, 0)
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
        self.object_registry = SimpleNamespace(is_registered_object=lambda _obj: True)
        self._focus = None
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.focus_state = FocusStateController(self)
        self.lock_state = LockStateController(self)
        self.lock_state.resolve = lambda: self.locking_object

    def _resolve_locking_state(self):
        return self.locking_object

    def _get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        return pos

    def enforce_point_lock(self, _pos):
        return None

    def event(self, event_type: Event, **kwargs: object):
        return SimpleGuiEvent(event_type, **kwargs)

    def update_focus(self, widget):
        self._focus = widget

    def update_active_window(self):
        self.focus_state.update_active_window()

    def _convert_to_window(self, point, _window):
        return point

    def handle_widget(self, _widget, _event, _window=None):
        return True

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None


class SchedulerGuiStub:
    pass


class CanvasGuiStub:
    def __init__(self) -> None:
        self.mouse_pos = (5, 5)
        self.locking_object = None
        self.mouse_locked = False

    def _get_mouse_pos(self):
        return self.mouse_pos

    def _convert_to_window(self, point, _window):
        return point


class EventDispatcherTests(unittest.TestCase):
    def test_keydown_becomes_framework_keydown_event(self) -> None:
        gui = EventDispatcherGuiStub()
        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(KEYDOWN, {"key": 77})

        event = dispatcher.handle(raw)

        self.assertEqual(event.type, Event.KeyDown)
        self.assertEqual(event.key, 77)

    def test_locked_widget_routes_widget_event(self) -> None:
        gui = EventDispatcherGuiStub()
        dispatcher = EventDispatcher(gui)

        class LockWidget:
            id = "locked"
            window = None

        widget = LockWidget()
        gui.locking_object = widget
        gui.widgets.append(widget)

        raw = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (2, 2)})
        event = dispatcher.handle(raw)

        self.assertEqual(event.type, Event.Widget)
        self.assertEqual(event.widget_id, "locked")


class SchedulerMessageFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_dispatch_limit_processes_messages_across_updates(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_message_dispatch_limit(1)

        self.scheduler.send_message("task", "a")
        self.scheduler.send_message("task", "b")

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["a"])
        self.assertEqual(self.scheduler._task_message_counts.get("task"), 1)

        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["a", "b"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_stale_generation_message_is_dropped(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1

        self.scheduler.send_message("task", "old")
        self.scheduler._task_generation["task"] = 2

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, [])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))


class CanvasQueueTests(unittest.TestCase):
    def _build_canvas_without_display_init(self) -> Canvas:
        canvas = Canvas.__new__(Canvas)
        canvas._disabled = False
        canvas.gui = CanvasGuiStub()
        canvas.window = None
        canvas.draw_rect = Rect(0, 0, 20, 20)
        canvas.hit_rect = None
        canvas._events = deque([], maxlen=2)
        canvas.dropped_events = 0
        canvas.last_overflow = False
        canvas.on_overflow = None
        canvas.coalesce_motion_events = True
        canvas.queued_event = False
        canvas.CEvent = None
        return canvas

    def test_motion_events_are_coalesced(self) -> None:
        canvas = self._build_canvas_without_display_init()

        first = pygame.event.Event(MOUSEMOTION, {"rel": (1, 1), "pos": (3, 3)})
        second = pygame.event.Event(MOUSEMOTION, {"rel": (4, 5), "pos": (4, 4)})

        self.assertTrue(canvas.handle_event(first, None))
        self.assertTrue(canvas.handle_event(second, None))

        self.assertEqual(len(canvas._events), 1)
        self.assertEqual(canvas._events[0].type, CanvasEvent.MouseMotion)
        self.assertEqual(canvas._events[0].rel, (4, 5))

    def test_overflow_tracks_drops_and_invokes_handler(self) -> None:
        canvas = self._build_canvas_without_display_init()
        canvas._events = deque([], maxlen=1)
        canvas.coalesce_motion_events = False
        overflow_calls = []
        canvas.on_overflow = lambda dropped, total: overflow_calls.append((dropped, total))

        first = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (4, 4)})
        second = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (6, 6)})

        self.assertTrue(canvas.handle_event(first, None))
        self.assertTrue(canvas.handle_event(second, None))

        self.assertEqual(canvas.dropped_events, 1)
        self.assertEqual(canvas.last_overflow, True)
        self.assertEqual(overflow_calls, [(1, 1)])


if __name__ == "__main__":
    unittest.main()
