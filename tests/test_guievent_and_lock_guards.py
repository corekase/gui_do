import unittest

from pygame import Rect

from gui.utility.constants import Event, GuiError
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController
from gui.utility.guimanager import GuiEvent, GuiManager
from gui.utility.widget import Widget


class GuiEventAndLockGuardTests(unittest.TestCase):
    def test_guievent_normalizes_malformed_payloads(self) -> None:
        event = GuiEvent(
            Event.Widget,
            key=True,
            pos=("x", 2),
            rel=(1,),
            button=1.25,
            widget_id=99,
            group=["g"],
            task_panel="yes",
        )

        self.assertIsNone(event.key)
        self.assertIsNone(event.pos)
        self.assertIsNone(event.rel)
        self.assertIsNone(event.button)
        self.assertIsNone(event.widget_id)
        self.assertIsNone(event.group)
        self.assertFalse(event.task_panel)

    def test_guievent_keeps_valid_payloads(self) -> None:
        event = GuiEvent(
            Event.MouseMotion,
            key=4,
            pos=(10, 11),
            rel=(2, 3),
            button=1,
            widget_id="w1",
            group="g1",
            task_panel=True,
        )

        self.assertEqual(event.key, 4)
        self.assertEqual(event.pos, (10, 11))
        self.assertEqual(event.rel, (2, 3))
        self.assertEqual(event.button, 1)
        self.assertEqual(event.widget_id, "w1")
        self.assertEqual(event.group, "g1")
        self.assertTrue(event.task_panel)

    def test_guimanager_event_injects_mouse_position_for_mouse_events(self) -> None:
        gui = GuiManager.__new__(GuiManager)
        gui.input_emitter = InputEventEmitter(gui)
        gui.drag_state = DragStateController(gui)
        gui.lock_state = LockStateController(gui)
        gui.get_mouse_pos = lambda: (7, 8)

        event = GuiManager.event(gui, Event.MouseButtonDown, button=1)

        self.assertEqual(event.pos, (7, 8))
        self.assertEqual(event.button, 1)

    def test_set_lock_area_release_clears_lock_state(self) -> None:
        gui = GuiManager.__new__(GuiManager)
        gui.input_emitter = InputEventEmitter(gui)
        gui.drag_state = DragStateController(gui)
        gui.lock_state = LockStateController(gui)
        lock_widget = Widget.__new__(Widget)

        gui.locking_object = lock_widget
        gui.mouse_locked = True
        gui.mouse_point_locked = True
        gui.lock_area_rect = Rect(0, 0, 10, 10)
        gui.lock_point_pos = (4, 5)
        gui.lock_point_recenter_pending = True
        gui.lock_point_tolerance_rect = Rect(0, 0, 3, 3)
        gui.mouse_pos = (9, 9)
        set_calls = []
        gui._set_physical_mouse_pos = lambda pos: set_calls.append(pos)

        GuiManager.set_lock_area(gui, None)

        self.assertEqual(set_calls, [(4, 5)])
        self.assertIsNone(gui.locking_object)
        self.assertFalse(gui.mouse_locked)
        self.assertFalse(gui.mouse_point_locked)
        self.assertIsNone(gui.lock_area_rect)
        self.assertIsNone(gui.lock_point_pos)
        self.assertFalse(gui.lock_point_recenter_pending)
        self.assertIsNone(gui.lock_point_tolerance_rect)

    def test_set_lock_point_rejects_non_widget_lock_owner(self) -> None:
        gui = GuiManager.__new__(GuiManager)
        gui.input_emitter = InputEventEmitter(gui)
        gui.drag_state = DragStateController(gui)
        gui.lock_state = LockStateController(gui)
        gui._is_registered_object = lambda _obj: False

        with self.assertRaises(GuiError):
            GuiManager.set_lock_point(gui, object(), (1, 2))

    def test_set_lock_point_uses_mouse_provider_when_point_missing(self) -> None:
        gui = GuiManager.__new__(GuiManager)
        gui.input_emitter = InputEventEmitter(gui)
        gui.drag_state = DragStateController(gui)
        gui.lock_state = LockStateController(gui)
        lock_widget = Widget.__new__(Widget)
        gui._is_registered_object = lambda obj: obj is lock_widget
        gui._mouse_get_pos = lambda: (12, 13)

        GuiManager.set_lock_point(gui, lock_widget)

        self.assertIs(gui.locking_object, lock_widget)
        self.assertTrue(gui.mouse_locked)
        self.assertTrue(gui.mouse_point_locked)
        self.assertEqual(gui.lock_point_pos, (12, 13))
        self.assertIsNone(gui.lock_area_rect)


if __name__ == "__main__":
    unittest.main()
