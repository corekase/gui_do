import unittest
import math

import pygame

from demo_features.moving_shapes.moving_shapes_backdrop_feature import MovingShapesBackdropFeature
from demo_features.moving_shapes.moving_shapes_specs import MOVING_SHAPES_MIN_SPEED
from demo_features.moving_shapes.moving_shapes_specs import MOVING_SHAPES_SPEED_BASE
from demo_features.moving_shapes.shape_sprite_state import ShapeSpriteState


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

    def test_create_shapes_applies_minimum_velocity_magnitude(self):
        feature = MovingShapesBackdropFeature(total_shapes=12, seed=9)

        for shape in feature._shapes:
            speed = math.hypot(shape.velocity_x, shape.velocity_y)
            self.assertGreaterEqual(speed + 1e-9, MOVING_SHAPES_MIN_SPEED * 1.10 + MOVING_SHAPES_SPEED_BASE)

    def test_bind_runtime_randomizes_positions_within_bounds(self):
        feature = MovingShapesBackdropFeature(total_shapes=3, seed=11)
        host = _StubHost(220, 160)

        feature.bind_runtime(host)

        for shape in feature._shapes:
            self.assertGreaterEqual(shape.center_x, shape.radius)
            self.assertLessEqual(shape.center_x, host.screen_rect.width - shape.radius)
            self.assertGreaterEqual(shape.center_y, shape.radius)
            self.assertLessEqual(shape.center_y, host.screen_rect.height - shape.radius)

    def test_on_direct_update_bounces_off_edges(self):
        feature = MovingShapesBackdropFeature(total_shapes=0, seed=3)
        sprite = pygame.Surface((20, 20), pygame.SRCALPHA)
        shape = ShapeSpriteState(
            radius=10,
            sprite=sprite,
            center_x=10.0,
            center_y=10.0,
            velocity_x=-120.0,
            velocity_y=-60.0,
        )
        feature._shapes = [shape]
        host = _StubHost(120, 100)

        feature.on_direct_update(host, 0.016)

        self.assertEqual(10.0, shape.center_x)
        self.assertEqual(10.0, shape.center_y)
        self.assertGreater(shape.velocity_x, 0.0)
        self.assertGreater(shape.velocity_y, 0.0)

    def test_on_direct_update_scales_motion_by_elapsed_time(self):
        feature = MovingShapesBackdropFeature(total_shapes=0, seed=5)
        sprite = pygame.Surface((20, 20), pygame.SRCALPHA)
        shape = ShapeSpriteState(
            radius=10,
            sprite=sprite,
            center_x=50.0,
            center_y=40.0,
            velocity_x=100.0,
            velocity_y=-50.0,
        )
        feature._shapes = [shape]
        host = _StubHost(300, 200)

        feature.on_direct_update(host, 0.25)

        self.assertAlmostEqual(75.0, shape.center_x)
        self.assertAlmostEqual(27.5, shape.center_y)


if __name__ == "__main__":
    unittest.main()
