import unittest

from pygame import Rect

from gui_manager_test_factory import build_gui_manager_stub
from gui.utility.events import Event, GuiError
from gui.utility.gui_utils.gui_event import GuiEvent
from gui.utility.gui_manager import GuiManager
from gui.utility.intermediates.widget import Widget


class GuiEventAndLockGuardTests(unittest.TestCase):
    def test_guievent_rejects_malformed_payloads(self) -> None:
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, key=True)
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, pos=("x", 2))
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, rel=(1,))
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, button=1.25)
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, widget_id=99)
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, group=["g"])
        with self.assertRaises(GuiError):
            GuiEvent(Event.Widget, task_panel="yes")

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
        gui = build_gui_manager_stub()
        gui._get_mouse_pos = lambda: (7, 8)

        event = GuiManager.event(gui, Event.MouseButtonDown, button=1)

        self.assertEqual(event.pos, (7, 8))
        self.assertEqual(event.button, 1)

    def test_set_lock_area_release_clears_lock_state(self) -> None:
        gui = build_gui_manager_stub()
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
        gui.pointer.set_physical_mouse_pos = lambda pos: set_calls.append(pos)

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
        gui = build_gui_manager_stub()
        gui.object_registry.is_registered_object = lambda _obj: False

        with self.assertRaises(GuiError):
            GuiManager.set_lock_point(gui, object(), (1, 2))

    def test_set_lock_point_uses_mouse_provider_when_point_missing(self) -> None:
        gui = build_gui_manager_stub()
        lock_widget = Widget.__new__(Widget)
        gui.object_registry.is_registered_object = lambda obj: obj is lock_widget
        gui.input_providers.mouse_get_pos = lambda: (12, 13)

        GuiManager.set_lock_point(gui, lock_widget)

        self.assertIs(gui.locking_object, lock_widget)
        self.assertTrue(gui.mouse_locked)
        self.assertTrue(gui.mouse_point_locked)
        self.assertEqual(gui.lock_point_pos, (12, 13))
        self.assertIsNone(gui.lock_area_rect)


if __name__ == "__main__":
    unittest.main()
