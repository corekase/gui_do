"""Life demo feature package.

This package is the canonical container for the Game of Life feature.
"""

from .life_feature import LifeFeature

FEATURE_PACKAGE_INFO = {
    "feature_name": "life",
    "scene_scope": "main",
    "layout_standard": "feature package with package-local specs and class modules",
}

__all__ = [
    "FEATURE_PACKAGE_INFO",
    "LifeFeature",
]
