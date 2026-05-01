"""Tests for InputSnapshot — immutable per-frame input state."""
import unittest

from gui_do.events.input_snapshot import InputSnapshot


# ===========================================================================
# InputSnapshot — construction and defaults
# ===========================================================================


class TestInputSnapshotDefaults(unittest.TestCase):
    def test_default_pointer_pos(self):
        s = InputSnapshot()
        self.assertEqual((0, 0), s.pointer_pos)

    def test_default_buttons_held_empty(self):
        s = InputSnapshot()
        self.assertEqual(frozenset(), s.buttons_held)

    def test_default_wheel_delta_zero(self):
        s = InputSnapshot()
        self.assertEqual(0.0, s.accumulated_wheel_delta)

    def test_default_hover_chain_empty(self):
        s = InputSnapshot()
        self.assertEqual((), s.hover_chain)

    def test_default_modifiers_zero(self):
        s = InputSnapshot()
        self.assertEqual(0, s.modifiers)


class TestInputSnapshotCustom(unittest.TestCase):
    def test_custom_pointer_pos(self):
        s = InputSnapshot(pointer_pos=(100, 200))
        self.assertEqual((100, 200), s.pointer_pos)

    def test_custom_buttons_held(self):
        s = InputSnapshot(buttons_held=frozenset({1, 3}))
        self.assertTrue(s.is_button_held(1))
        self.assertTrue(s.is_button_held(3))
        self.assertFalse(s.is_button_held(2))

    def test_custom_hover_chain(self):
        s = InputSnapshot(hover_chain=("outer", "inner"))
        self.assertEqual(("outer", "inner"), s.hover_chain)

    def test_wheel_delta_stored(self):
        s = InputSnapshot(accumulated_wheel_delta=3.5)
        self.assertEqual(3.5, s.accumulated_wheel_delta)


# ===========================================================================
# InputSnapshot — convenience queries
# ===========================================================================


class TestInputSnapshotQueries(unittest.TestCase):
    def test_is_button_just_pressed(self):
        s = InputSnapshot(buttons_just_pressed=frozenset({1}))
        self.assertTrue(s.is_button_just_pressed(1))
        self.assertFalse(s.is_button_just_pressed(3))

    def test_is_button_just_released(self):
        s = InputSnapshot(buttons_just_released=frozenset({2}))
        self.assertTrue(s.is_button_just_released(2))
        self.assertFalse(s.is_button_just_released(1))

    def test_is_key_just_pressed(self):
        s = InputSnapshot(keys_just_pressed=frozenset({65}))
        self.assertTrue(s.is_key_just_pressed(65))
        self.assertFalse(s.is_key_just_pressed(66))

    def test_is_key_just_released(self):
        s = InputSnapshot(keys_just_released=frozenset({13}))
        self.assertTrue(s.is_key_just_released(13))
        self.assertFalse(s.is_key_just_released(14))

    def test_is_key_down_modifier_flag(self):
        s = InputSnapshot(modifiers=0x0001)
        self.assertTrue(s.is_key_down(0x0001))
        self.assertFalse(s.is_key_down(0x0002))

    def test_topmost_hovered_id_empty(self):
        s = InputSnapshot()
        self.assertIsNone(s.topmost_hovered_id)

    def test_topmost_hovered_id_returns_last(self):
        s = InputSnapshot(hover_chain=("panel", "button"))
        self.assertEqual("button", s.topmost_hovered_id)

    def test_pointer_delta_stored(self):
        s = InputSnapshot(pointer_delta=(5, -3))
        self.assertEqual((5, -3), s.pointer_delta)


if __name__ == "__main__":
    unittest.main()
