import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_parts.bouncing_shapes_demo_part import BouncingShapesBackdropFeature


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

    def set_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None, scene_name=None) -> None:
        del scene_name
        self._screen_preamble = preamble
        self._screen_event_handler = event_handler
        self._screen_postamble = postamble

    def chain_screen_lifecycle(self, preamble=None, event_handler=None, postamble=None, scene_name=None):
        del scene_name
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


class BouncingShapesBackdropFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_init_creates_requested_circle_count_with_cached_sprites(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=12, seed=7)

        self.assertEqual(len(part._shapes), 12)
        self.assertTrue(all(shape.sprite is not None for shape in part._shapes))

    def test_init_supports_diamond_count_and_combines_shape_total(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=5, diamond_count=7, seed=11)

        self.assertEqual(part.circle_count, 5)
        self.assertEqual(part.diamond_count, 7)
        self.assertEqual(len(part._shapes), 12)

    def test_init_randomizes_mixed_shape_draw_order(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=8, diamond_count=8, seed=19)
        kinds = [shape.kind for shape in part._shapes]

        self.assertIn("circle", kinds)
        self.assertIn("diamond", kinds)
        self.assertNotEqual(kinds[:8], ["circle"] * 8)
        self.assertNotEqual(kinds[:8], ["diamond"] * 8)

    def test_screen_postamble_bounces_circle_at_edge(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=1, seed=3)
        host = SimpleNamespace(app=_StubApp((120, 80)), screen_rect=pygame.Rect(0, 0, 120, 80))
        part.bind_runtime(host)

        circle = part._shapes[0]
        circle.radius = 10
        circle.x = 10.0
        circle.y = 20.0
        circle.dx = -2.0
        circle.dy = 0.0

        part.screen_postamble()

        self.assertGreater(circle.dx, 0.0)
        self.assertEqual(circle.x, 10.0)

    def test_screen_preamble_composes_and_sets_pristine(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=2, seed=9)
        app = _StubApp((200, 140))
        host = SimpleNamespace(app=app, screen_rect=pygame.Rect(0, 0, 200, 140))
        part.bind_runtime(host)

        part.screen_preamble()

        self.assertEqual(app._set_pristine_calls, 1)
        self.assertIsNotNone(app._last_pristine)

    def test_unregister_disposes_lifecycle_chain(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=1, seed=1)
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
