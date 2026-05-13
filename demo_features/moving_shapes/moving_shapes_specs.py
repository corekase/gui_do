"""Shared specs and constants for the bouncing shapes demo feature."""

DEMO_SHAPE_COLOURS = (
    (220, 60, 60),
    (220, 140, 60),
    (220, 220, 60),
    (60, 190, 100),
    (60, 170, 220),
    (120, 120, 230),
    (190, 120, 220),
    (235, 115, 170),
)
DEMO_BORDER_BASE_COLOUR = (0, 0, 0)

MOVING_SHAPES_DEFINITIONS: tuple[tuple[int, bool], ...] = (
    (0, False),
    (3, False),
    (4, False),
    (5, False),
    (6, False),
    (8, False),
    (5, True),
)

MOVING_SHAPES_RADIUS_RANGE = (12, 38)
MOVING_SHAPES_ALPHA_RANGE = (150, 230)
MOVING_SHAPES_SPEED_BASE = 2.8
MOVING_SHAPES_SPEED_VARIANCE = 1.8

__all__ = [
    "DEMO_BORDER_BASE_COLOUR",
    "DEMO_SHAPE_COLOURS",
    "MOVING_SHAPES_ALPHA_RANGE",
    "MOVING_SHAPES_DEFINITIONS",
    "MOVING_SHAPES_RADIUS_RANGE",
    "MOVING_SHAPES_SPEED_BASE",
    "MOVING_SHAPES_SPEED_VARIANCE",
]
