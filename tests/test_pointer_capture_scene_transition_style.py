"""Tests for PointerCapture and SceneTransitionStyle."""
import unittest
import pygame
from pygame import Rect

from gui_do.events.pointer_capture import PointerCapture
from gui_do.persistence.scene_transition_manager import SceneTransitionStyle

pygame.init()


# ===========================================================================
# SceneTransitionStyle
# ===========================================================================


class TestSceneTransitionStyle(unittest.TestCase):
    def test_none_value(self):
        self.assertEqual("none", SceneTransitionStyle.NONE.value)

    def test_fade_value(self):
        self.assertEqual("fade", SceneTransitionStyle.FADE.value)

    def test_slide_left(self):
        self.assertEqual("slide_left", SceneTransitionStyle.SLIDE_LEFT.value)

    def test_slide_right(self):
        self.assertEqual("slide_right", SceneTransitionStyle.SLIDE_RIGHT.value)

    def test_slide_up(self):
        self.assertEqual("slide_up", SceneTransitionStyle.SLIDE_UP.value)

    def test_slide_down(self):
        self.assertEqual("slide_down", SceneTransitionStyle.SLIDE_DOWN.value)


# ===========================================================================
# PointerCapture
# ===========================================================================


class TestPointerCaptureInitial(unittest.TestCase):
    def test_owner_id_none(self):
        pc = PointerCapture()
        self.assertIsNone(pc.owner_id)

    def test_is_active_false(self):
        pc = PointerCapture()
        self.assertFalse(pc.is_active)

    def test_lock_rect_none(self):
        pc = PointerCapture()
        self.assertIsNone(pc.lock_rect)

    def test_use_relative_motion_false(self):
        pc = PointerCapture()
        self.assertFalse(pc.use_relative_motion)


class TestPointerCaptureBeginEnd(unittest.TestCase):
    def test_begin_sets_owner(self):
        pc = PointerCapture()
        pc.begin("slider", Rect(0, 0, 100, 100))
        self.assertEqual("slider", pc.owner_id)

    def test_begin_sets_is_active(self):
        pc = PointerCapture()
        pc.begin("slider", Rect(0, 0, 100, 100))
        self.assertTrue(pc.is_active)

    def test_begin_stores_rect(self):
        pc = PointerCapture()
        r = Rect(10, 20, 80, 60)
        pc.begin("slider", r)
        self.assertEqual(r, pc.lock_rect)

    def test_begin_relative_motion(self):
        pc = PointerCapture()
        pc.begin("drag", Rect(0, 0, 200, 200), use_relative_motion=True)
        self.assertTrue(pc.use_relative_motion)

    def test_end_clears_owner(self):
        pc = PointerCapture()
        pc.begin("slider", Rect(0, 0, 100, 100))
        pc.end("slider")
        self.assertIsNone(pc.owner_id)
        self.assertFalse(pc.is_active)

    def test_end_wrong_owner_no_effect(self):
        pc = PointerCapture()
        pc.begin("slider", Rect(0, 0, 100, 100))
        pc.end("other")
        self.assertEqual("slider", pc.owner_id)

    def test_is_owned_by_true(self):
        pc = PointerCapture()
        pc.begin("slider", Rect(0, 0, 100, 100))
        self.assertTrue(pc.is_owned_by("slider"))

    def test_is_owned_by_false(self):
        pc = PointerCapture()
        pc.begin("slider", Rect(0, 0, 100, 100))
        self.assertFalse(pc.is_owned_by("other"))


class TestPointerCaptureForceRelease(unittest.TestCase):
    def test_force_release_returns_owner(self):
        pc = PointerCapture()
        pc.begin("drag_widget", Rect(0, 0, 200, 200))
        prev = pc.force_release()
        self.assertEqual("drag_widget", prev)

    def test_force_release_clears(self):
        pc = PointerCapture()
        pc.begin("drag", Rect(0, 0, 100, 100))
        pc.force_release()
        self.assertFalse(pc.is_active)

    def test_force_release_when_idle_returns_none(self):
        pc = PointerCapture()
        result = pc.force_release()
        self.assertIsNone(result)


class TestPointerCaptureClamp(unittest.TestCase):
    def test_clamp_no_lock_rect_passthrough(self):
        pc = PointerCapture()
        self.assertEqual((50, 60), pc.clamp((50, 60)))

    def test_clamp_inside_rect(self):
        pc = PointerCapture()
        pc.begin("x", Rect(10, 10, 100, 80))
        self.assertEqual((50, 50), pc.clamp((50, 50)))

    def test_clamp_below_min_x(self):
        pc = PointerCapture()
        pc.begin("x", Rect(10, 10, 100, 80))
        x, y = pc.clamp((0, 50))
        self.assertEqual(10, x)

    def test_clamp_above_max_x(self):
        pc = PointerCapture()
        pc.begin("x", Rect(10, 10, 100, 80))
        x, y = pc.clamp((200, 50))
        self.assertEqual(109, x)  # right - 1 = 110 - 1 = 109

    def test_clamp_above_max_y(self):
        pc = PointerCapture()
        pc.begin("x", Rect(0, 0, 100, 80))
        x, y = pc.clamp((50, 200))
        self.assertEqual(79, y)   # bottom - 1 = 80 - 1 = 79


if __name__ == "__main__":
    unittest.main()
