import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONUP

from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from gui.utility.intermediates.widget import Widget
from state_model_backed_stub import StateModelBackedStub


class _WindowStub:
    def __init__(self, x: int = 30, y: int = 40) -> None:
        self.x = x
        self.y = y

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, value):
        self.x, self.y = value

    def get_title_bar_rect(self):
        return Rect(0, 0, 200, 20)

    def get_widget_rect(self):
        return Rect(500, 500, 10, 10)


class _GuiStub(StateModelBackedStub):
    def __init__(self) -> None:
        self._init_state_models()
        self.locking_object = None
        self.mouse_locked = False
        self.mouse_point_locked = False
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
        self.mouse_pos = (10, 10)
        self.point_lock_recenter_rect = Rect(0, 0, 100, 100)

        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.active_window = None
        self.windows = []

        self.object_registry = SimpleNamespace(is_registered_object=lambda _obj: True)
        self.input_providers = SimpleNamespace(mouse_get_pos=lambda: (9, 9))
        self.pointer_calls = []
        self.pointer = SimpleNamespace(set_physical_mouse_pos=lambda pos: self.pointer_calls.append(pos))

        self.lowered = []
        self.lock_area = lambda pos: pos
        self.lower_window = lambda window: self.lowered.append(window)
        self.get_mouse_pos = lambda: self.mouse_pos
        self.set_mouse_pos_calls = []

        def _set_mouse_pos(pos, update_physical_coords=True):
            self.mouse_pos = pos
            self.set_mouse_pos_calls.append((pos, update_physical_coords))

        self.set_mouse_pos = _set_mouse_pos


class InputStateSyncContractsTests(unittest.TestCase):
    def test_lock_set_area_updates_lock_state_model(self) -> None:
        gui = _GuiStub()
        controller = LockStateController(gui)
        locking_object = Widget.__new__(Widget)

        controller.set_area(locking_object, Rect(1, 2, 5, 6))

        self.assertIs(gui._lock_state.locking_object, gui.locking_object)
        self.assertEqual(gui._lock_state.lock_area_rect, gui.lock_area_rect)
        self.assertEqual(gui._lock_state.mouse_locked, gui.mouse_locked)
        self.assertEqual(gui._lock_state.mouse_point_locked, gui.mouse_point_locked)

    def test_lock_release_resets_lock_state_model(self) -> None:
        gui = _GuiStub()
        controller = LockStateController(gui)
        locking_object = Widget.__new__(Widget)
        controller.set_point(locking_object, (4, 5))

        controller.set_area(None)

        self.assertIsNone(gui._lock_state.locking_object)
        self.assertIsNone(gui.locking_object)
        self.assertEqual(gui._lock_state.mouse_locked, gui.mouse_locked)
        self.assertEqual(gui._lock_state.lock_point_pos, gui.lock_point_pos)

    def test_drag_start_updates_drag_state_model(self) -> None:
        gui = _GuiStub()
        controller = DragStateController(gui)
        window = _WindowStub(100, 120)
        gui.active_window = window
        gui.windows = [window]
        gui.mouse_pos = (20, 30)

        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (10, 10)})
        controller.start_if_possible(event)

        self.assertEqual(gui._drag_state.dragging, gui.dragging)
        self.assertIs(gui._drag_state.dragging_window, gui.dragging_window)
        self.assertEqual(gui._drag_state.mouse_delta, gui.mouse_delta)

    def test_drag_release_updates_drag_state_model(self) -> None:
        gui = _GuiStub()
        controller = DragStateController(gui)
        window = _WindowStub(30, 40)
        gui.windows = [window]
        gui.dragging = True
        gui.dragging_window = window
        gui.mouse_delta = (3, 4)

        event = pygame.event.Event(MOUSEBUTTONUP, {'button': 1})
        controller.handle_drag_event(event)

        self.assertEqual(gui._drag_state.dragging, gui.dragging)
        self.assertIs(gui._drag_state.dragging_window, gui.dragging_window)
        self.assertEqual(gui._drag_state.mouse_delta, gui.mouse_delta)


if __name__ == '__main__':
    unittest.main()
