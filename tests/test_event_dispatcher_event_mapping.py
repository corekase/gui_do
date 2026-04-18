import unittest

import pygame
from pygame.locals import KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, QUIT

from gui.utility.constants import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class SimpleGuiEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class MappingGuiStub:
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
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.focus_state = FocusStateController(self)
        self.lock_state = LockStateController(self)

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        return pos

    def enforce_point_lock(self, _pos):
        return None

    def event(self, event_type: Event, **kwargs: object):
        return SimpleGuiEvent(event_type, **kwargs)

    def update_focus(self, _widget):
        return None

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, _widget, _event, _window=None):
        return False

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherEventMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gui = MappingGuiStub()
        self.dispatcher = EventDispatcher(self.gui)

    def _emit(self, action):
        return self.dispatcher.emitter.emit_action(action)

    def test_system_event_mappings(self) -> None:
        quit_event = pygame.event.Event(QUIT, {})
        keydown_event = pygame.event.Event(KEYDOWN, {"key": 123})
        keyup_event = pygame.event.Event(KEYUP, {"key": 99})

        mapped_quit = self._emit(self.dispatcher.router._handle_system_event(quit_event))
        mapped_down = self._emit(self.dispatcher.router._handle_system_event(keydown_event))
        mapped_up = self._emit(self.dispatcher.router._handle_system_event(keyup_event))

        self.assertEqual(mapped_quit.type, Event.Quit)
        self.assertEqual(mapped_down.type, Event.KeyDown)
        self.assertEqual(mapped_down.key, 123)
        self.assertEqual(mapped_up.type, Event.KeyUp)
        self.assertEqual(mapped_up.key, 99)

    def test_system_event_defaults_missing_key_to_none(self) -> None:
        keydown_event = pygame.event.Event(KEYDOWN, {})
        keyup_event = pygame.event.Event(KEYUP, {})

        mapped_down = self._emit(self.dispatcher.router._handle_system_event(keydown_event))
        mapped_up = self._emit(self.dispatcher.router._handle_system_event(keyup_event))

        self.assertEqual(mapped_down.type, Event.KeyDown)
        self.assertIsNone(mapped_down.key)
        self.assertEqual(mapped_up.type, Event.KeyUp)
        self.assertIsNone(mapped_up.key)

    def test_base_mouse_mappings_and_defaults(self) -> None:
        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        up = pygame.event.Event(MOUSEBUTTONUP, {"button": 3})
        motion_with_rel = pygame.event.Event(MOUSEMOTION, {"rel": (4, -2)})
        motion_without_rel = pygame.event.Event(MOUSEMOTION, {})

        mapped_down = self._emit(self.dispatcher.router.targets._handle_base_mouse_events(down))
        mapped_up = self._emit(self.dispatcher.router.targets._handle_base_mouse_events(up))
        mapped_motion = self._emit(self.dispatcher.router.targets._handle_base_mouse_events(motion_with_rel))
        mapped_motion_default = self._emit(self.dispatcher.router.targets._handle_base_mouse_events(motion_without_rel))

        self.assertEqual(mapped_down.type, Event.MouseButtonDown)
        self.assertEqual(mapped_down.button, 1)
        self.assertEqual(mapped_up.type, Event.MouseButtonUp)
        self.assertEqual(mapped_up.button, 3)
        self.assertEqual(mapped_motion.type, Event.MouseMotion)
        self.assertEqual(mapped_motion.rel, (4, -2))
        self.assertEqual(mapped_motion_default.rel, (0, 0))

    def test_unhandled_base_event_returns_pass(self) -> None:
        unknown = pygame.event.Event(KEYDOWN, {"key": 1})

        mapped = self._emit(self.dispatcher.router.targets._handle_base_mouse_events(unknown))

        self.assertEqual(mapped.type, Event.Pass)


if __name__ == "__main__":
    unittest.main()
