import unittest

from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.events.input_snapshot import InputSnapshot


def _mouse_down(button: int, pos=(10, 20), mod: int = 0) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, button=button, pos=pos, mod=mod)


def _mouse_up(button: int, pos=(10, 20), mod: int = 0) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, button=button, pos=pos, mod=mod)


def _mouse_motion(pos=(30, 40), rel=(5, -3)) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=pos, rel=rel)


def _mouse_wheel(delta: int) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_WHEEL, type=0, wheel_y=delta)


def _key_down(key: int, mod: int = 0) -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_DOWN, type=0, key=key, mod=mod)


def _key_up(key: int, mod: int = 0) -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_UP, type=0, key=key, mod=mod)


class TestInputSnapshotBuild(unittest.TestCase):
    def test_empty_snapshot_has_zero_state(self):
        snap = InputSnapshot.build(events=[])

        self.assertEqual((0, 0), snap.pointer_pos)
        self.assertEqual((0, 0), snap.pointer_delta)
        self.assertFalse(snap.is_button_held(1))
        self.assertFalse(snap.is_button_just_pressed(1))
        self.assertFalse(snap.is_button_just_released(1))
        self.assertEqual(0.0, snap.accumulated_wheel_delta)
        self.assertIsNone(snap.topmost_hovered_id)

    def test_mouse_button_down_sets_held_and_just_pressed(self):
        snap = InputSnapshot.build(events=[_mouse_down(1)])

        self.assertTrue(snap.is_button_held(1))
        self.assertTrue(snap.is_button_just_pressed(1))
        self.assertFalse(snap.is_button_just_released(1))

    def test_mouse_button_up_sets_just_released_and_clears_held(self):
        previous = InputSnapshot.build(events=[_mouse_down(1)])
        snap = InputSnapshot.build(events=[_mouse_up(1)], previous=previous)

        self.assertFalse(snap.is_button_held(1))
        self.assertTrue(snap.is_button_just_released(1))
        self.assertFalse(snap.is_button_just_pressed(1))

    def test_previous_held_buttons_carry_forward(self):
        previous = InputSnapshot.build(events=[_mouse_down(1)])
        snap = InputSnapshot.build(events=[], previous=previous)

        self.assertTrue(snap.is_button_held(1))
        self.assertFalse(snap.is_button_just_pressed(1))

    def test_mouse_motion_updates_pointer_pos_and_delta(self):
        snap = InputSnapshot.build(events=[_mouse_motion(pos=(30, 40), rel=(5, -3))])

        self.assertEqual((30, 40), snap.pointer_pos)
        self.assertEqual((5, -3), snap.pointer_delta)

    def test_mouse_motion_delta_is_accumulated_across_multiple_events(self):
        events = [
            _mouse_motion(pos=(10, 10), rel=(3, 2)),
            _mouse_motion(pos=(15, 13), rel=(5, 3)),
        ]
        snap = InputSnapshot.build(events=events)

        self.assertEqual((15, 13), snap.pointer_pos)
        self.assertEqual((8, 5), snap.pointer_delta)

    def test_wheel_delta_accumulated_across_events(self):
        events = [_mouse_wheel(2), _mouse_wheel(1)]
        snap = InputSnapshot.build(events=events)

        self.assertAlmostEqual(3.0, snap.accumulated_wheel_delta)

    def test_key_down_adds_to_keys_just_pressed(self):
        snap = InputSnapshot.build(events=[_key_down(65)])

        self.assertTrue(snap.is_key_just_pressed(65))
        self.assertFalse(snap.is_key_just_released(65))

    def test_key_up_adds_to_keys_just_released(self):
        snap = InputSnapshot.build(events=[_key_up(65)])

        self.assertFalse(snap.is_key_just_pressed(65))
        self.assertTrue(snap.is_key_just_released(65))

    def test_modifier_bitmask_set_from_key_events(self):
        snap = InputSnapshot.build(events=[_key_down(304, mod=0x0001)])  # LSHIFT

        self.assertTrue(snap.is_key_down(0x0001))
        self.assertFalse(snap.is_key_down(0x0040))  # LCTRL not held

    def test_pointer_pos_updated_by_mouse_button_down(self):
        snap = InputSnapshot.build(events=[_mouse_down(1, pos=(55, 66))])

        self.assertEqual((55, 66), snap.pointer_pos)

    def test_topmost_hovered_id_returns_last_chain_element(self):
        snap = InputSnapshot.empty().with_hover_chain(("panel", "button"))

        self.assertEqual("button", snap.topmost_hovered_id)

    def test_topmost_hovered_id_returns_none_for_empty_chain(self):
        snap = InputSnapshot.empty()

        self.assertIsNone(snap.topmost_hovered_id)

    def test_empty_factory_produces_zero_state_snapshot(self):
        snap = InputSnapshot.empty()

        self.assertEqual((0, 0), snap.pointer_pos)
        self.assertFalse(snap.is_button_held(1))
        self.assertEqual(frozenset(), snap.keys_just_pressed)


if __name__ == "__main__":
    unittest.main()
