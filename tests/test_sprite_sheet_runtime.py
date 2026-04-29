"""Tests for SpriteSheet and FrameAnimation."""
import unittest

import pygame
from pygame import Surface

from gui_do.graphics.sprite_sheet import SpriteSheet, FrameAnimation


def _sheet_surface(cols: int, rows: int, fw: int = 32, fh: int = 32) -> Surface:
    pygame.init()
    return Surface((cols * fw, rows * fh))


class TestSpriteSheetConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_frame_count(self) -> None:
        surf = _sheet_surface(4, 2, 32, 32)
        sheet = SpriteSheet(surf, frame_w=32, frame_h=32)
        self.assertEqual(sheet.frame_count, 8)

    def test_invalid_frame_size_raises(self) -> None:
        surf = _sheet_surface(1, 1)
        with self.assertRaises(ValueError):
            SpriteSheet(surf, frame_w=0, frame_h=32)

    def test_frame_surface_correct_size(self) -> None:
        surf = _sheet_surface(4, 2, 32, 32)
        sheet = SpriteSheet(surf, frame_w=32, frame_h=32)
        frame = sheet.frame(0)
        self.assertEqual(frame.get_size(), (32, 32))

    def test_frame_surface_out_of_range_raises(self) -> None:
        surf = _sheet_surface(2, 1, 32, 32)
        sheet = SpriteSheet(surf, frame_w=32, frame_h=32)
        with self.assertRaises((IndexError, ValueError)):
            sheet.frame(99)

    def test_frame_surface_cached(self) -> None:
        surf = _sheet_surface(4, 2, 32, 32)
        sheet = SpriteSheet(surf, frame_w=32, frame_h=32)
        s1 = sheet.frame(0)
        s2 = sheet.frame(0)
        self.assertIs(s1, s2)


class TestFrameAnimationConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def _sheet(self) -> SpriteSheet:
        return SpriteSheet(_sheet_surface(4, 1, 32, 32), frame_w=32, frame_h=32)

    def test_frame_count(self) -> None:
        anim = FrameAnimation(sheet=self._sheet(), frames=[0, 1, 2, 3], fps=12)
        self.assertEqual(len(anim.frames), 4)

    def test_initial_frame_index(self) -> None:
        anim = FrameAnimation(sheet=self._sheet(), frames=[0, 1, 2, 3], fps=12)
        self.assertEqual(anim.current_frame_index, 0)

    def test_is_playing_by_default(self) -> None:
        anim = FrameAnimation(sheet=self._sheet(), frames=[0, 1], fps=12)
        self.assertTrue(anim.is_playing)

    def test_not_complete_initially(self) -> None:
        anim = FrameAnimation(sheet=self._sheet(), frames=[0, 1], fps=12, loop=False)
        self.assertFalse(anim.is_complete)

    def test_current_surface_is_surface(self) -> None:
        anim = FrameAnimation(sheet=self._sheet(), frames=[0, 1, 2], fps=12)
        self.assertIsInstance(anim.current_surface, Surface)


class TestFrameAnimationPlayback(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def _anim(self, fps: float = 10.0, loop: bool = True) -> FrameAnimation:
        sheet = SpriteSheet(_sheet_surface(4, 1, 32, 32), frame_w=32, frame_h=32)
        return FrameAnimation(sheet=sheet, frames=[0, 1, 2, 3], fps=fps, loop=loop)

    def test_update_advances_frame_at_fps(self) -> None:
        anim = self._anim(fps=10.0)
        anim.update(0.11)  # slightly more than 1/10 s
        self.assertEqual(anim.current_frame_index, 1)

    def test_update_wraps_when_looping(self) -> None:
        anim = self._anim(fps=10.0, loop=True)
        for _ in range(50):
            anim.update(0.11)
        # Should have looped back without error
        self.assertGreaterEqual(anim.current_frame_index, 0)

    def test_complete_when_non_loop_finished(self) -> None:
        anim = self._anim(fps=100.0, loop=False)
        for _ in range(10):
            anim.update(0.11)
        self.assertTrue(anim.is_complete)

    def test_pause_stops_advance(self) -> None:
        anim = self._anim(fps=10.0)
        anim.pause()
        anim.update(1.0)
        self.assertEqual(anim.current_frame_index, 0)

    def test_play_resumes_after_pause(self) -> None:
        anim = self._anim(fps=10.0)
        anim.pause()
        anim.play()
        anim.update(0.11)
        self.assertEqual(anim.current_frame_index, 1)

    def test_reset_returns_to_frame_zero(self) -> None:
        anim = self._anim(fps=10.0)
        anim.update(0.3)
        anim.reset()
        self.assertEqual(anim.current_frame_index, 0)

    def test_seek_frame(self) -> None:
        anim = self._anim(fps=10.0)
        anim.seek_frame(2)
        self.assertEqual(anim.current_frame_index, 2)

    def test_on_complete_callback_fired(self) -> None:
        called = []
        sheet = SpriteSheet(_sheet_surface(2, 1, 32, 32), frame_w=32, frame_h=32)
        anim = FrameAnimation(
            sheet=sheet,
            frames=[0, 1],
            fps=100.0,
            loop=False,
            on_complete=lambda: called.append(True),
        )
        for _ in range(10):
            anim.update(0.1)
        self.assertTrue(called)
