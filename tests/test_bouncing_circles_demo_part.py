import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_parts.bouncing_circles_demo_part import BouncingCirclesBackdropFeature


class _StubApp:
    def __init__(self, size) -> None:
        self._screen_preamble = None
        self._screen_event_handler = None
        self._screen_postamble = None
        self.theme = SimpleNamespace(background=(10, 10, 10))
        self._set_pristine_calls = 0
        self._last_pristine = None
        self._size = size

    def restore_pristine(self, scene_name=None, surface=None) -> bool:
        if surface is not None:
            surface.fill((20, 20, 20))
        return True

    def set_pristine(self, source, scene_name=None) -> None:
        self._set_pristine_calls += 1
        self._last_pristine = source.copy()

    def set_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None) -> None:
        self._screen_preamble = preamble
        self._screen_event_handler = event_handler
        self._screen_postamble = postamble

    def chain_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None):
        previous_preamble = self._screen_preamble
        previous_postamble = self._screen_postamble

        if previous_preamble is None:
            self._screen_preamble = preamble
        elif preamble is None:
            self._screen_preamble = previous_preamble
        else:
            def _chained_preamble() -> None:
                previous_preamble()
                preamble()

            self._screen_preamble = _chained_preamble

        if previous_postamble is None:
            self._screen_postamble = postamble
        elif postamble is None:
            self._screen_postamble = previous_postamble
        else:
            def _chained_postamble() -> None:
                previous_postamble()
                postamble()

            self._screen_postamble = _chained_postamble

        disposed = False

        def _dispose() -> bool:
            nonlocal disposed
            if disposed:
                return False
            disposed = True
            self._screen_preamble = previous_preamble
            self._screen_postamble = previous_postamble
            return True

        return _dispose


class BouncingCirclesBackdropFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_init_creates_requested_circle_count_with_cached_sprites(self) -> None:
        part = BouncingCirclesBackdropFeature(circle_count=12, seed=7)

        self.assertEqual(len(part._circles), 12)
        self.assertTrue(all(circle.sprite is not None for circle in part._circles))

    def test_screen_postamble_bounces_circle_at_edge(self) -> None:
        part = BouncingCirclesBackdropFeature(circle_count=1, seed=3)
        host = SimpleNamespace(app=_StubApp((120, 80)), screen_rect=pygame.Rect(0, 0, 120, 80))
        part.bind_runtime(host)

        circle = part._circles[0]
        circle.radius = 10
        circle.x = 10.0
        circle.y = 20.0
        circle.dx = -2.0
        circle.dy = 0.0

        part.screen_postamble()

        self.assertGreater(circle.dx, 0.0)
        self.assertEqual(circle.x, 10.0)

    def test_screen_preamble_composes_and_sets_pristine(self) -> None:
        part = BouncingCirclesBackdropFeature(circle_count=2, seed=9)
        app = _StubApp((200, 140))
        host = SimpleNamespace(app=app, screen_rect=pygame.Rect(0, 0, 200, 140))
        part.bind_runtime(host)

        part.screen_preamble()

        self.assertEqual(app._set_pristine_calls, 1)
        self.assertIsNotNone(app._last_pristine)

    def test_unregister_disposes_lifecycle_chain(self) -> None:
        part = BouncingCirclesBackdropFeature(circle_count=1, seed=1)
        app = _StubApp((200, 140))
        host = SimpleNamespace(app=app, screen_rect=pygame.Rect(0, 0, 200, 140))

        part.bind_runtime(host)

        self.assertTrue(callable(app._screen_preamble))
        self.assertTrue(callable(app._screen_postamble))

        part.on_unregister(host)

        self.assertIsNone(app._screen_preamble)
        self.assertIsNone(app._screen_postamble)


if __name__ == "__main__":
    unittest.main()
