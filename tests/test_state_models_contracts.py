import unittest

from pygame import Rect

from gui.utility.gui_utils.drag_state_model import DragState
from gui.utility.gui_utils.lock_state_model import LockState
from gui.utility.intermediates.widget import Widget
from gui.widgets.window import Window


class DragStateContractsTests(unittest.TestCase):
    def test_start_drag_and_stop_drag_form_consistent_state(self) -> None:
        state = DragState()
        window = Widget.__new__(Widget)  # only type identity needed for this model test

        with self.assertRaises(ValueError):
            state.start_drag(window, (1, 2))  # type: ignore[arg-type]

    def test_start_drag_requires_int_delta(self) -> None:
        state = DragState()
        window = Window.__new__(Window)

        with self.assertRaises(ValueError):
            state.start_drag(window, (1.0, 2))  # type: ignore[arg-type]


class LockStateContractsTests(unittest.TestCase):
    def test_apply_area_lock_validates_geometry(self) -> None:
        state = LockState()
        owner = Widget.__new__(Widget)

        with self.assertRaises(ValueError):
            state.apply_area_lock(owner, Rect(0, 0, 0, 2))

    def test_apply_area_lock_and_clear_lock(self) -> None:
        state = LockState()
        owner = Widget.__new__(Widget)

        state.apply_area_lock(owner, Rect(1, 2, 5, 6))
        self.assertTrue(state.has_active_lock())
        self.assertFalse(state.mouse_point_locked)
        self.assertEqual(state.lock_area_rect, Rect(1, 2, 5, 6))

        state.clear_lock()
        self.assertFalse(state.has_active_lock())
        self.assertIsNone(state.lock_area_rect)

    def test_apply_point_lock_requires_int_tuple(self) -> None:
        state = LockState()
        owner = Widget.__new__(Widget)

        with self.assertRaises(ValueError):
            state.apply_point_lock(owner, (3.5, 2))  # type: ignore[arg-type]

    def test_recenter_pending_requires_bool(self) -> None:
        state = LockState()
        with self.assertRaises(ValueError):
            state.set_recenter_pending(1)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
