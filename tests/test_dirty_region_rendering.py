"""Tests for dirty-region rendering infrastructure (Feature 6)."""
import unittest
from unittest.mock import MagicMock, patch, call

import pygame
from pygame import Rect

from gui_do.core.invalidation import InvalidationTracker


class TestInvalidateAllSetsFullRedraw(unittest.TestCase):
    def test_invalidate_all_sets_full_redraw(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear the initial full_redraw
        self.assertFalse(tracker.begin_frame()[0])
        tracker.invalidate_all()
        is_full, rects = tracker.begin_frame()
        self.assertTrue(is_full)
        self.assertEqual(rects, [])


class TestInvalidateRectAddsToList(unittest.TestCase):
    def test_invalidate_rect_adds_to_dirty_list(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear initial full_redraw
        r = Rect(10, 20, 50, 30)
        tracker.invalidate_rect(r)
        is_full, rects = tracker.begin_frame()
        self.assertFalse(is_full)
        self.assertEqual(len(rects), 1)
        self.assertEqual(rects[0], r)


class TestInvalidateAllClearsRects(unittest.TestCase):
    def test_invalidate_all_clears_rect_list(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.invalidate_rect(Rect(20, 20, 10, 10))
        _, rects_before = tracker.begin_frame()
        self.assertEqual(len(rects_before), 2)
        tracker.invalidate_all()
        is_full, rects_after = tracker.begin_frame()
        self.assertTrue(is_full)
        self.assertEqual(rects_after, [])


class TestEndFrameClearsDirtyState(unittest.TestCase):
    def test_end_frame_clears_dirty_state(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 5, 5))
        tracker.end_frame()
        is_full, rects = tracker.begin_frame()
        self.assertFalse(is_full)
        self.assertEqual(rects, [])


class TestFullRectPromotesToFullRedraw(unittest.TestCase):
    def test_full_rect_promotes_to_full_redraw(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.set_screen_size((800, 600))
        # Rect equal to screen size should promote to full redraw
        tracker.invalidate_rect(Rect(0, 0, 800, 600))
        is_full, rects = tracker.begin_frame()
        self.assertTrue(is_full)
        self.assertEqual(rects, [])


class TestMergeDirtyRectsOverlapping(unittest.TestCase):
    def test_merge_dirty_rects_combines_overlapping(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 50, 50))
        tracker.invalidate_rect(Rect(40, 40, 50, 50))  # overlaps first
        merged = tracker.merge_dirty_rects()
        self.assertEqual(len(merged), 1)
        union = Rect(0, 0, 50, 50).union(Rect(40, 40, 50, 50))
        self.assertEqual(merged[0], union)

    def test_merge_dirty_rects_keeps_non_overlapping(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.invalidate_rect(Rect(100, 100, 10, 10))
        merged = tracker.merge_dirty_rects()
        self.assertEqual(len(merged), 2)


class TestEngineUsesDisplayUpdate(unittest.TestCase):
    def test_engine_uses_display_update_when_dirty_rects_returned(self) -> None:
        """When app.draw() returns a non-empty list, engine uses display.update."""
        from gui_do.loop.ui_engine import UiEngine
        dirty = [Rect(0, 0, 10, 10)]
        mock_app = MagicMock()
        mock_app.running = True
        mock_app.draw.return_value = dirty

        # Make the loop run exactly one iteration then stop
        call_count = [0]
        def fake_tick(fps):
            call_count[0] += 1
            if call_count[0] >= 1:
                mock_app.running = False
            return 16
        engine = UiEngine(mock_app, target_fps=60)
        engine.clock = MagicMock()
        engine.clock.tick.side_effect = fake_tick

        with patch('pygame.event.get', return_value=[]), \
             patch('pygame.display.update') as mock_update, \
             patch('pygame.display.flip') as mock_flip:
            engine.run(max_frames=1)
            mock_update.assert_called_once_with(dirty)
            mock_flip.assert_not_called()


class TestEngineUsesDisplayFlip(unittest.TestCase):
    def test_engine_uses_display_flip_when_full_redraw(self) -> None:
        """When app.draw() returns None, engine uses display.flip."""
        from gui_do.loop.ui_engine import UiEngine
        mock_app = MagicMock()
        mock_app.running = True
        mock_app.draw.return_value = None

        call_count = [0]
        def fake_tick(fps):
            call_count[0] += 1
            if call_count[0] >= 1:
                mock_app.running = False
            return 16
        engine = UiEngine(mock_app, target_fps=60)
        engine.clock = MagicMock()
        engine.clock.tick.side_effect = fake_tick

        with patch('pygame.event.get', return_value=[]), \
             patch('pygame.display.update') as mock_update, \
             patch('pygame.display.flip') as mock_flip:
            engine.run(max_frames=1)
            mock_flip.assert_called_once()
            mock_update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
