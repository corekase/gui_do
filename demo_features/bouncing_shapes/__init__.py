"""Bouncing shapes demo feature package.

This package is the canonical container for the bouncing-shapes feature.
Feature-specific classes, specs, and future helpers should live here.
"""

from .bouncing_shapes_backdrop_feature import (
    BouncingShapesBackdropFeature,
)
from .bouncing_shapes_specs import DEMO_BORDER_BASE_COLOUR, DEMO_SHAPE_COLOURS
from .shape_sprite_state import ShapeSpriteState

FEATURE_PACKAGE_INFO = {
    "feature_name": "bouncing_shapes",
    "scene_scope": "all",
    "layout_standard": "feature package with package-local specs and class modules",
}

__all__ = [
    "BouncingShapesBackdropFeature",
    "DEMO_BORDER_BASE_COLOUR",
    "DEMO_SHAPE_COLOURS",
    "FEATURE_PACKAGE_INFO",
    "ShapeSpriteState",
]
