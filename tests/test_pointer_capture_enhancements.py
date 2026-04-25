"""Tests for PointerCapture.is_active and force_release."""
import unittest

from pygame import Rect

from gui.core.pointer_capture import PointerCapture


class PointerCaptureIsActiveTests(unittest.TestCase):

    def test_is_active_false_on_fresh_instance(self) -> None:
        pc = PointerCapture()
        self.assertFalse(pc.is_active)

    def test_is_active_true_after_begin(self) -> None:
        pc = PointerCapture()
        pc.begin("drag_a", Rect(0, 0, 200, 200))
        self.assertTrue(pc.is_active)

    def test_is_active_false_after_matching_end(self) -> None:
        pc = PointerCapture()
        pc.begin("drag_a", Rect(0, 0, 100, 100))
        pc.end("drag_a")
        self.assertFalse(pc.is_active)

    def test_is_active_true_after_non_matching_end(self) -> None:
        pc = PointerCapture()
        pc.begin("owner_a", Rect(0, 0, 100, 100))
        pc.end("owner_b")  # wrong owner — capture stays
        self.assertTrue(pc.is_active)

    def test_is_active_false_after_force_release(self) -> None:
        pc = PointerCapture()
        pc.begin("owner", Rect(0, 0, 50, 50))
        pc.force_release()
        self.assertFalse(pc.is_active)


class PointerCaptureForceReleaseTests(unittest.TestCase):

    def test_force_release_returns_previous_owner_id(self) -> None:
        pc = PointerCapture()
        pc.begin("slider_x", Rect(0, 0, 300, 20))
        result = pc.force_release()
        self.assertEqual(result, "slider_x")

    def test_force_release_returns_none_when_not_active(self) -> None:
        pc = PointerCapture()
        result = pc.force_release()
        self.assertIsNone(result)

    def test_force_release_clears_owner_id(self) -> None:
        pc = PointerCapture()
        pc.begin("w", Rect(0, 0, 10, 10))
        pc.force_release()
        self.assertIsNone(pc.owner_id)

    def test_force_release_clears_lock_rect(self) -> None:
        pc = PointerCapture()
        pc.begin("w", Rect(5, 10, 100, 50))
        pc.force_release()
        self.assertIsNone(pc.lock_rect)

    def test_force_release_releases_even_without_matching_owner(self) -> None:
        pc = PointerCapture()
        pc.begin("owner_a", Rect(0, 0, 100, 100))
        # Normally end("owner_b") would not release; force_release must always clear
        previous = pc.force_release()
        self.assertEqual(previous, "owner_a")
        self.assertFalse(pc.is_active)

    def test_force_release_followed_by_new_begin_works(self) -> None:
        pc = PointerCapture()
        pc.begin("first", Rect(0, 0, 100, 100))
        pc.force_release()
        pc.begin("second", Rect(10, 10, 50, 50))
        self.assertTrue(pc.is_active)
        self.assertEqual(pc.owner_id, "second")

    def test_force_release_idempotent(self) -> None:
        pc = PointerCapture()
        pc.force_release()  # on idle capture — must not raise
        self.assertFalse(pc.is_active)

    def test_clamp_passes_through_after_force_release(self) -> None:
        pc = PointerCapture()
        pc.begin("w", Rect(0, 0, 50, 50))
        pc.force_release()
        pos = (200, 300)
        self.assertEqual(pc.clamp(pos), pos)


if __name__ == "__main__":
    unittest.main()
