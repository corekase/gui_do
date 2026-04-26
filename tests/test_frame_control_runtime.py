import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect, Surface

from gui_do.controls.frame_control import FrameControl


class _FakeFactory:
    def build_frame_visuals(self, rect: Rect):
        idle = Surface((rect.width, rect.height), pygame.SRCALPHA)
        idle.fill((200, 200, 200, 255))
        hover = idle.copy()
        armed = idle.copy()
        disabled = idle.copy()
        hidden = Surface((rect.width, rect.height), pygame.SRCALPHA)
        return SimpleNamespace(idle=idle, hover=hover, armed=armed, disabled=disabled, hidden=hidden)

    @staticmethod
    def resolve_visual_state(visuals, *, visible: bool, enabled: bool, armed: bool, hovered: bool):
        del armed, hovered
        if not visible:
            return visuals.hidden
        if not enabled:
            return visuals.disabled
        return visuals.idle


class FrameControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((320, 200))

    def tearDown(self) -> None:
        pygame.quit()

    def test_border_width_changes_drawn_border_thickness(self) -> None:
        control = FrameControl("frame", Rect(10, 10, 60, 40), border_width=3)
        theme = SimpleNamespace(graphics_factory=_FakeFactory(), dark=(5, 6, 7), medium=(80, 81, 82))
        target = Surface((120, 90), pygame.SRCALPHA)

        control.draw(target, theme)

        edge = target.get_at((10, 10))
        inner_border = target.get_at((12, 12))
        interior = target.get_at((14, 14))

        self.assertEqual(tuple(edge[:3]), (5, 6, 7))
        self.assertEqual(tuple(inner_border[:3]), (5, 6, 7))
        self.assertEqual(tuple(interior[:3]), (200, 200, 200))

    def test_hidden_frame_does_not_draw_border(self) -> None:
        control = FrameControl("frame", Rect(10, 10, 60, 40), border_width=2)
        control.visible = False
        theme = SimpleNamespace(graphics_factory=_FakeFactory(), dark=(5, 6, 7), medium=(80, 81, 82))
        target = Surface((120, 90), pygame.SRCALPHA)

        before = target.get_at((10, 10))
        control.draw(target, theme)
        after = target.get_at((10, 10))

        self.assertEqual(before, after)

    def test_disabled_frame_uses_medium_border_colour(self) -> None:
        control = FrameControl("frame", Rect(10, 10, 60, 40), border_width=1)
        control.enabled = False
        theme = SimpleNamespace(graphics_factory=_FakeFactory(), dark=(5, 6, 7), medium=(80, 81, 82))
        target = Surface((120, 90), pygame.SRCALPHA)

        control.draw(target, theme)

        edge = target.get_at((10, 10))
        self.assertEqual(tuple(edge[:3]), (80, 81, 82))


if __name__ == "__main__":
    unittest.main()
