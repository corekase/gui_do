import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui_do import GuiApplication
from gui_do import DirectFeature


class _TrackingDirectFeature(DirectFeature):
    def __init__(self) -> None:
        super().__init__("tracking_screen_part")
        self.screen_updates = 0
        self.screen_draws = 0
        self.screen_events = 0
        self.last_dt = None

    def on_direct_update(self, host, dt_seconds: float) -> None:
        del host
        self.screen_updates += 1
        self.last_dt = float(dt_seconds)

    def draw_direct(self, host, surface, theme) -> None:
        del host, theme
        self.screen_draws += 1
        surface.fill((255, 0, 0), pygame.Rect(0, 0, 4, 4))

    def handle_direct_event(self, host, event) -> bool:
        del host
        self.screen_events += 1
        return event.is_mouse_down(1)


class DirectFeatureRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((32, 32))
        self.surface = pygame.Surface((32, 32))
        self.app = GuiApplication(self.surface)
        self.feature = _TrackingDirectFeature()
        self.host = SimpleNamespace(app=self.app, screen_rect=self.surface.get_rect())
        self.app.register_feature(self.feature, host=self.host)
        self.app.bind_features_runtime(self.host)

    def tearDown(self) -> None:
        self.app.shutdown()
        pygame.quit()

    def test_screen_part_update_called_from_application_update(self) -> None:
        self.app.update(1.0 / 60.0)

        self.assertEqual(self.feature.screen_updates, 1)
        self.assertAlmostEqual(self.feature.last_dt, 1.0 / 60.0)

    def test_screen_part_draw_called_from_renderer_path(self) -> None:
        self.surface.fill((0, 0, 0))

        self.app.draw()

        self.assertEqual(self.feature.screen_draws, 1)
        painted = False
        for y in range(4):
            for x in range(4):
                if self.surface.get_at((x, y))[:3] == (255, 0, 0):
                    painted = True
                    break
            if painted:
                break
        self.assertTrue(painted)

    def test_screen_part_event_handler_runs_before_scene_dispatch(self) -> None:
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)})

        consumed = self.app.process_event(event)

        self.assertTrue(consumed)
        self.assertEqual(self.feature.screen_events, 1)


if __name__ == "__main__":
    unittest.main()
