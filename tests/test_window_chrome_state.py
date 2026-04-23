import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect, Surface

from gui.controls.window_control import WindowControl


class _FakeFactory:
    def build_frame_visuals(self, rect: Rect):
        idle = Surface((rect.width, rect.height), pygame.SRCALPHA)
        idle.fill((20, 20, 20, 255))
        hover = idle.copy()
        armed = idle.copy()
        disabled = idle.copy()
        hidden = Surface((rect.width, rect.height), pygame.SRCALPHA)
        return SimpleNamespace(idle=idle, hover=hover, armed=armed, disabled=disabled, hidden=hidden, hit_rect=Rect(rect))

    @staticmethod
    def resolve_visual_state(visuals, *, visible: bool, enabled: bool, armed: bool, hovered: bool):
        del visible, enabled, armed, hovered
        return visuals.idle

    @staticmethod
    def build_window_chrome_visuals(width: int, titlebar_height: int, title: str):
        del titlebar_height, title
        inactive = Surface((width, 24), pygame.SRCALPHA)
        inactive.fill((200, 0, 0, 255))
        active = Surface((width, 24), pygame.SRCALPHA)
        active.fill((0, 200, 0, 255))
        lower = Surface((24, 24), pygame.SRCALPHA)
        lower.fill((0, 0, 200, 255))
        return SimpleNamespace(title_bar_inactive=inactive, title_bar_active=active, lower_widget=lower)

    @staticmethod
    def build_disabled_bitmap(surface):
        return surface.copy()


class _FakeTheme:
    def __init__(self) -> None:
        self.graphics_factory = _FakeFactory()
        self.dark = (0, 0, 0)


class WindowChromeStateTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.display = pygame.display.set_mode((320, 200))

    def tearDown(self) -> None:
        pygame.quit()

    def test_draw_uses_active_titlebar_bitmap_when_window_is_active(self) -> None:
        window = WindowControl("win", Rect(20, 20, 200, 120), "W")
        window.set_active(True)
        target = Surface((320, 200), pygame.SRCALPHA)

        window.draw(target, _FakeTheme())

        sample = target.get_at((window.rect.left + 6, window.rect.top + 6))
        self.assertEqual(tuple(sample[:3]), (0, 200, 0))

    def test_draw_uses_inactive_titlebar_bitmap_when_window_is_inactive(self) -> None:
        window = WindowControl("win", Rect(20, 20, 200, 120), "W")
        window.set_active(False)
        target = Surface((320, 200), pygame.SRCALPHA)

        window.draw(target, _FakeTheme())

        sample = target.get_at((window.rect.left + 6, window.rect.top + 6))
        self.assertEqual(tuple(sample[:3]), (200, 0, 0))

    def test_restore_pristine_defaults_to_black_before_set_pristine(self) -> None:
        window = WindowControl("win", Rect(20, 20, 200, 120), "W")
        target = Surface((320, 200), pygame.SRCALPHA)

        restored = window.restore_pristine(target)

        self.assertTrue(restored)
        sample = target.get_at(window.rect.topleft)
        self.assertEqual(tuple(sample[:3]), (0, 0, 0))

    def test_set_pristine_overwrites_default_black_pristine(self) -> None:
        window = WindowControl("win", Rect(20, 20, 200, 120), "W")
        source = Surface((16, 16))
        source.fill((12, 34, 56))
        window.set_pristine(source)
        target = Surface((320, 200), pygame.SRCALPHA)

        restored = window.restore_pristine(target)

        self.assertTrue(restored)
        sample = target.get_at(window.rect.topleft)
        self.assertEqual(tuple(sample[:3]), (12, 34, 56))

    def test_restore_pristine_returns_false_when_frame_backdrop_mode_is_enabled(self) -> None:
        window = WindowControl("win", Rect(20, 20, 200, 120), "W", use_frame_backdrop=True)
        target = Surface((320, 200), pygame.SRCALPHA)

        restored = window.restore_pristine(target)

        self.assertFalse(restored)

    def test_draw_uses_frame_backdrop_when_frame_backdrop_mode_is_enabled(self) -> None:
        window = WindowControl("win", Rect(20, 20, 200, 120), "W", use_frame_backdrop=True)
        target = Surface((320, 200), pygame.SRCALPHA)

        window.draw(target, _FakeTheme())

        sample = target.get_at((window.rect.left + 40, window.rect.top + 40))
        self.assertEqual(tuple(sample[:3]), (20, 20, 20))


if __name__ == "__main__":
    unittest.main()
