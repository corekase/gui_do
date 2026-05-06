"""Systems demo feature package.

This package owns the systems feature, its specs, and feature-local support classes.
"""

from .system_feature import SystemFeature

FEATURE_PACKAGE_INFO = {
    "feature_name": "system",
    "scene_scope": "main",
    "layout_standard": "feature package with package-local specs, classes, and helpers",
}

__all__ = [
    "FEATURE_PACKAGE_INFO",
    "SystemFeature",
]
