"""Tests for InputSnapshot, InputState, and TextSpan."""
import unittest
from types import SimpleNamespace

import pygame

from gui_do.events.input_snapshot import InputSnapshot
from gui_do.events.input_state import InputState
from gui_do.events.gui_event import EventType
from gui_do.text.text_flow import TextSpan

pygame.init()


def _make_event(kind, pos=(0, 0), button=None, key=None, mod=0, wheel_delta=None, rel=None):
    return SimpleNamespace(kind=kind, pos=pos, button=button, key=key, mod=mod,
                           wheel_delta=wheel_delta, rel=rel)


# ===========================================================================
# TextSpan
# ===========================================================================


class TestTextSpan(unittest.TestCase):
    def test_text_stored(self):
        span = TextSpan("hello")
        self.assertEqual("hello", span.text)

    def test_defaults(self):
        span = TextSpan("hi")
        self.assertFalse(span.bold)
        self.assertFalse(span.italic)
        self.assertIsNone(span.color)
        self.assertEqual("body", span.role)

    def test_bold_stored(self):
        span = TextSpan("hi", bold=True)
        self.assertTrue(span.bold)

    def test_italic_stored(self):
        span = TextSpan("hi", italic=True)
        self.assertTrue(span.italic)

    def test_color_stored(self):
        span = TextSpan("hi", color=(255, 0, 0))
        self.assertEqual((255, 0, 0), span.color)

    def test_role_stored(self):
        span = TextSpan("hi", role="title")
        self.assertEqual("title", span.role)


# ===========================================================================
# InputState
# ===========================================================================


class TestInputState(unittest.TestCase):
    def test_initial_pointer_pos(self):
        state = InputState()
        self.assertEqual((0, 0), state.pointer_pos)

    def test_update_from_event(self):
        state = InputState()
        event = SimpleNamespace(pos=(100, 200))
        state.update_from_event(event)
        self.assertEqual((100, 200), state.pointer_pos)

    def test_update_ignores_invalid_pos(self):
        state = InputState()
        event = SimpleNamespace(pos="bad")
        state.update_from_event(event)
        self.assertEqual((0, 0), state.pointer_pos)


# ===========================================================================
# InputSnapshot — constructor defaults
# ===========================================================================


class TestInputSnapshotDefaults(unittest.TestCase):
    def test_default_pointer_pos(self):
        snap = InputSnapshot()
        self.assertEqual((0, 0), snap.pointer_pos)

    def test_default_pointer_delta(self):
        snap = InputSnapshot()
        self.assertEqual((0, 0), snap.pointer_delta)

    def test_default_buttons_held_empty(self):
        snap = InputSnapshot()
        self.assertEqual(frozenset(), snap.buttons_held)

    def test_default_hover_chain_empty(self):
        snap = InputSnapshot()
        self.assertEqual((), snap.hover_chain)

    def test_topmost_hovered_id_none(self):
        snap = InputSnapshot()
        self.assertIsNone(snap.topmost_hovered_id)

    def test_topmost_hovered_id_present(self):
        snap = InputSnapshot(hover_chain=("a", "b", "c"))
        self.assertEqual("c", snap.topmost_hovered_id)


# ===========================================================================
# InputSnapshot — convenience queries
# ===========================================================================


class TestInputSnapshotQueries(unittest.TestCase):
    def test_is_button_held_true(self):
        snap = InputSnapshot(buttons_held=frozenset({1}))
        self.assertTrue(snap.is_button_held(1))

    def test_is_button_held_false(self):
        snap = InputSnapshot()
        self.assertFalse(snap.is_button_held(1))

    def test_is_button_just_pressed(self):
        snap = InputSnapshot(buttons_just_pressed=frozenset({1}))
        self.assertTrue(snap.is_button_just_pressed(1))

    def test_is_button_just_released(self):
        snap = InputSnapshot(buttons_just_released=frozenset({3}))
        self.assertTrue(snap.is_button_just_released(3))

    def test_is_key_down_true(self):
        snap = InputSnapshot(modifiers=0x01)
        self.assertTrue(snap.is_key_down(0x01))

    def test_is_key_down_false(self):
        snap = InputSnapshot(modifiers=0)
        self.assertFalse(snap.is_key_down(0x01))

    def test_is_key_just_pressed(self):
        snap = InputSnapshot(keys_just_pressed=frozenset({97}))
        self.assertTrue(snap.is_key_just_pressed(97))

    def test_is_key_just_released(self):
        snap = InputSnapshot(keys_just_released=frozenset({97}))
        self.assertTrue(snap.is_key_just_released(97))


# ===========================================================================
# InputSnapshot.build()
# ===========================================================================


class TestInputSnapshotBuild(unittest.TestCase):
    def test_build_empty_events(self):
        snap = InputSnapshot.build(events=[])
        self.assertEqual((0, 0), snap.pointer_pos)

    def test_build_mouse_down(self):
        ev = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(50, 60), button=1)
        snap = InputSnapshot.build(events=[ev])
        self.assertEqual((50, 60), snap.pointer_pos)
        self.assertIn(1, snap.buttons_held)
        self.assertIn(1, snap.buttons_just_pressed)

    def test_build_mouse_up_removes_held(self):
        ev_down = _make_event(EventType.MOUSE_BUTTON_DOWN, pos=(0, 0), button=1)
        ev_up = _make_event(EventType.MOUSE_BUTTON_UP, pos=(0, 0), button=1)
        snap = InputSnapshot.build(events=[ev_down, ev_up])
        self.assertNotIn(1, snap.buttons_held)
        self.assertIn(1, snap.buttons_just_released)

    def test_build_mouse_motion_updates_pos(self):
        ev = _make_event(EventType.MOUSE_MOTION, pos=(30, 40), rel=(5, 10))
        snap = InputSnapshot.build(events=[ev])
        self.assertEqual((30, 40), snap.pointer_pos)
        self.assertEqual((5, 10), snap.pointer_delta)

    def test_build_wheel_accumulates(self):
        ev1 = _make_event(EventType.MOUSE_WHEEL, wheel_delta=3)
        ev2 = _make_event(EventType.MOUSE_WHEEL, wheel_delta=2)
        snap = InputSnapshot.build(events=[ev1, ev2])
        self.assertEqual(5.0, snap.accumulated_wheel_delta)

    def test_build_key_down(self):
        ev = _make_event(EventType.KEY_DOWN, key=97)
        snap = InputSnapshot.build(events=[ev])
        self.assertIn(97, snap.keys_just_pressed)

    def test_build_key_up(self):
        ev = _make_event(EventType.KEY_UP, key=97)
        snap = InputSnapshot.build(events=[ev])
        self.assertIn(97, snap.keys_just_released)

    def test_build_with_previous_pos(self):
        prev = InputSnapshot(pointer_pos=(10, 20))
        snap = InputSnapshot.build(events=[], previous=prev)
        self.assertEqual((10, 20), snap.pointer_pos)

    def test_build_with_previous_held(self):
        prev = InputSnapshot(buttons_held=frozenset({1}))
        snap = InputSnapshot.build(events=[], previous=prev)
        self.assertIn(1, snap.buttons_held)


if __name__ == "__main__":
    unittest.main()
