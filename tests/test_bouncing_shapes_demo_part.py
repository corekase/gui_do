import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_parts.bouncing_shapes_demo_part import BouncingShapesBackdropFeature
from shared.part_lifecycle import ScreenPart


class BouncingShapesBackdropFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_feature_is_screen_part(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=1, seed=7)
        self.assertIsInstance(part, ScreenPart)

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

    def test_bind_runtime_randomizes_positions_using_screen_bounds(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=3, seed=3)
        host = SimpleNamespace(app=SimpleNamespace(), screen_rect=pygame.Rect(0, 0, 120, 80))

        part.bind_runtime(host)

        for shape in part._shapes:
            self.assertGreaterEqual(shape.x, float(shape.radius))
            self.assertLessEqual(shape.x, float(120 - shape.radius))
            self.assertGreaterEqual(shape.y, float(shape.radius))
            self.assertLessEqual(shape.y, float(80 - shape.radius))

    def test_on_screen_update_bounces_circle_at_edge(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=1, seed=3)
        host = SimpleNamespace(app=SimpleNamespace(), screen_rect=pygame.Rect(0, 0, 120, 80))
        part.bind_runtime(host)

        circle = part._shapes[0]
        circle.radius = 10
        circle.x = 10.0
        circle.y = 20.0
        circle.dx = -2.0
        circle.dy = 0.0

        part.on_screen_update(host, 1.0 / 60.0)

        self.assertGreater(circle.dx, 0.0)
        self.assertEqual(circle.x, 10.0)

    def test_draw_screen_blits_shapes_to_surface(self) -> None:
        part = BouncingShapesBackdropFeature(circle_count=1, seed=1)
        host = SimpleNamespace(app=SimpleNamespace(), screen_rect=pygame.Rect(0, 0, 120, 80))
        part.bind_runtime(host)

        surface = pygame.Surface((120, 80), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        before = surface.get_at((int(part._shapes[0].x), int(part._shapes[0].y)))

        part.draw_screen(host, surface, None)

        after = surface.get_at((int(part._shapes[0].x), int(part._shapes[0].y)))
        self.assertNotEqual(before, after)

    def test_host_requirements_restore_screen_runtime_contract(self) -> None:
        self.assertEqual(BouncingShapesBackdropFeature.HOST_REQUIREMENTS["bind_runtime"], ("app", "screen_rect"))


if __name__ == "__main__":
    unittest.main()
