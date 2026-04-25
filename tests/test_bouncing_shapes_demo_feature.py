import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_features.bouncing_shapes_demo_feature import BouncingShapesBackdropFeature
from shared.feature_lifecycle import DirectFeature


class BouncingShapesBackdropFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_feature_is_screen_part(self) -> None:
        feature = BouncingShapesBackdropFeature(circle_count=1, seed=7)
        self.assertIsInstance(feature, DirectFeature)

    def test_init_creates_requested_circle_count_with_cached_sprites(self) -> None:
        feature = BouncingShapesBackdropFeature(circle_count=12, seed=7)

        self.assertEqual(len(feature._shapes), 12)
        self.assertTrue(all(shape.sprite is not None for shape in feature._shapes))

    def test_init_supports_shape_counts_and_combines_shape_total(self) -> None:
        feature = BouncingShapesBackdropFeature(
            circle_count=5,
            square_count=3,
            octagon_count=2,
            star_count=4,
            seed=11,
        )

        self.assertEqual(feature.circle_count, 5)
        self.assertEqual(feature.square_count, 3)
        self.assertEqual(feature.octagon_count, 2)
        self.assertEqual(feature.star_count, 4)
        self.assertEqual(len(feature._shapes), 14)

    def test_init_randomizes_mixed_shape_draw_order(self) -> None:
        feature = BouncingShapesBackdropFeature(
            circle_count=8,
            square_count=8,
            octagon_count=8,
            star_count=8,
            seed=19,
        )
        kinds = [shape.kind for shape in feature._shapes]

        self.assertIn("circle", kinds)
        self.assertIn("square", kinds)
        self.assertIn("octagon", kinds)
        self.assertIn("star", kinds)
        self.assertNotEqual(kinds[:8], ["circle"] * 8)
        self.assertNotEqual(kinds[:8], ["square"] * 8)

    def test_bind_runtime_randomizes_positions_using_screen_bounds(self) -> None:
        feature = BouncingShapesBackdropFeature(circle_count=3, seed=3)
        host = SimpleNamespace(app=SimpleNamespace(), screen_rect=pygame.Rect(0, 0, 120, 80))

        feature.bind_runtime(host)

        for shape in feature._shapes:
            self.assertGreaterEqual(shape.x, float(shape.radius))
            self.assertLessEqual(shape.x, float(120 - shape.radius))
            self.assertGreaterEqual(shape.y, float(shape.radius))
            self.assertLessEqual(shape.y, float(80 - shape.radius))

    def test_on_direct_update_bounces_circle_at_edge(self) -> None:
        feature = BouncingShapesBackdropFeature(circle_count=1, seed=3)
        host = SimpleNamespace(app=SimpleNamespace(), screen_rect=pygame.Rect(0, 0, 120, 80))
        feature.bind_runtime(host)

        circle = feature._shapes[0]
        circle.radius = 10
        circle.x = 10.0
        circle.y = 20.0
        circle.dx = -2.0
        circle.dy = 0.0

        feature.on_direct_update(host, 1.0 / 60.0)

        self.assertGreater(circle.dx, 0.0)
        self.assertEqual(circle.x, 10.0)

    def test_draw_screen_blits_shapes_to_surface(self) -> None:
        feature = BouncingShapesBackdropFeature(circle_count=1, seed=1)
        host = SimpleNamespace(app=SimpleNamespace(), screen_rect=pygame.Rect(0, 0, 120, 80))
        feature.bind_runtime(host)

        surface = pygame.Surface((120, 80), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        before = surface.get_at((int(feature._shapes[0].x), int(feature._shapes[0].y)))

        feature.draw_direct(host, surface, None)

        after = surface.get_at((int(feature._shapes[0].x), int(feature._shapes[0].y)))
        self.assertNotEqual(before, after)

    def test_host_requirements_restore_screen_runtime_contract(self) -> None:
        self.assertEqual(BouncingShapesBackdropFeature.HOST_REQUIREMENTS["bind_runtime"], ("app", "screen_rect"))


if __name__ == "__main__":
    unittest.main()
