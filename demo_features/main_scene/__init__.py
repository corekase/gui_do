"""Main scene demo feature package.

This package is the canonical container for the demo's main-scene feature.
Feature-specific classes, specs, and future helpers should live here as a best-practice layout.
"""

from .main_demo_feature import MainDemoFeature
from .main_specs import MAIN_RUNTIME_SPEC

FEATURE_PACKAGE_INFO = {
    "feature_name": "main_scene",
    "scene_scope": "main",
    "layout_best_practice": "keep main-scene classes, specs, and helpers inside this package",
}

__all__ = [
    "FEATURE_PACKAGE_INFO",
    "MAIN_RUNTIME_SPEC",
    "MainDemoFeature",
]
