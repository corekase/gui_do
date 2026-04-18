import unittest

import pygame
from pygame.locals import MOUSEMOTION

from gui.utility.event_dispatcher import EventDispatcher


class MouseLockGuiStub:
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
        self.mouse_pos = (10, 10)
        self.enforced = []
        self.locked_inputs = []

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        self.locked_inputs.append(pos)
        x = max(0, min(100, pos[0]))
        y = max(0, min(100, pos[1]))
        return (x, y)

    def enforce_point_lock(self, pos):
        self.enforced.append(pos)

    def event(self, _event_type, **_kwargs):
        event = type("GuiEvent", (), {})()
        return event

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


class EventDispatcherMouseLockBatch10Tests(unittest.TestCase):
    def test_mouse_motion_unlocked_uses_event_position_only(self) -> None:
        gui = MouseLockGuiStub()
        gui.mouse_locked = False
        dispatcher = EventDispatcher(gui)

        dispatcher._handle_mouse_motion(pygame.event.Event(MOUSEMOTION, {"rel": (5, 7), "pos": (120, -10)}))

        self.assertEqual(gui.locked_inputs, [(120, -10)])
        self.assertEqual(gui.mouse_pos, (100, 0))
        self.assertEqual(gui.enforced, [])

    def test_mouse_motion_locked_uses_delta_and_enforces_point_lock(self) -> None:
        gui = MouseLockGuiStub()
        gui.mouse_locked = True
        gui.mouse_pos = (90, 95)
        dispatcher = EventDispatcher(gui)

        dispatcher._handle_mouse_motion(pygame.event.Event(MOUSEMOTION, {"rel": (20, 10), "pos": (200, 150)}))

        self.assertEqual(gui.locked_inputs, [(110, 105)])
        self.assertEqual(gui.mouse_pos, (100, 100))
        self.assertEqual(gui.enforced, [(200, 150)])


if __name__ == "__main__":
    unittest.main()
