"""Controls showcase demo feature package.

This package owns the showcase feature, its specs, and feature-local support classes.
"""

from .showcase_feature import ShowcaseFeature

FEATURE_PACKAGE_INFO = {
    "feature_name": "showcase",
    "scene_scope": "control_showcase",
    "layout_standard": "feature package with package-local specs, classes, and helpers",
}

__all__ = [
    "ShowcaseFeature",
    "FEATURE_PACKAGE_INFO",
]
