import unittest

import pygame

from demo_features.moving_shapes import MovingShapesBackdropFeature, ShapeSpriteState


class _StubHost:
    def __init__(self, width: int, height: int):
        self.screen_rect = pygame.Rect(0, 0, int(width), int(height))


class TestBouncingShapesDemoFeature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_create_shapes_respects_requested_counts(self):
        feature = MovingShapesBackdropFeature(total_shapes=7, seed=7)

        self.assertEqual(7, len(feature._shapes))

    def test_bind_runtime_randomizes_positions_within_bounds(self):
        feature = MovingShapesBackdropFeature(total_shapes=3, seed=11)
        host = _StubHost(220, 160)

        feature.bind_runtime(host)

        for shape in feature._shapes:
            self.assertGreaterEqual(shape.x, shape.radius)
            self.assertLessEqual(shape.x, host.screen_rect.width - shape.radius)
            self.assertGreaterEqual(shape.y, shape.radius)
            self.assertLessEqual(shape.y, host.screen_rect.height - shape.radius)

    def test_on_direct_update_bounces_off_edges(self):
        feature = MovingShapesBackdropFeature(total_shapes=0, seed=3)
        sprite = pygame.Surface((20, 20), pygame.SRCALPHA)
        shape = ShapeSpriteState(
            radius=10,
            sprite=sprite,
            x=10.0,
            y=10.0,
            dx=-2.0,
            dy=-1.0,
        )
        feature._shapes = [shape]
        host = _StubHost(120, 100)

        feature.on_direct_update(host, 0.016)

        self.assertEqual(10.0, shape.x)
        self.assertEqual(10.0, shape.y)
        self.assertGreater(shape.dx, 0.0)
        self.assertGreater(shape.dy, 0.0)


if __name__ == "__main__":
    unittest.main()
