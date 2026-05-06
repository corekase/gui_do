"""Moving shapes demo feature package.

This package is the canonical container for the moving-shapes feature.
Feature-specific classes, specs, and future helpers should live here.
"""

from .moving_shapes_backdrop_feature import (
    MovingShapesBackdropFeature,
)
from .shape_sprite_state import ShapeSpriteState

FEATURE_PACKAGE_INFO = {
    "feature_name": "moving_shapes",
    "scene_scope": "all",
    "layout_standard": "feature package with package-local specs and class modules",
}

__all__ = [
    "MovingShapesBackdropFeature",
    "FEATURE_PACKAGE_INFO",
    "ShapeSpriteState",
]
