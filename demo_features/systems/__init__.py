"""Systems demo feature package.

This package owns the systems feature, its specs, and feature-local support classes.
"""

from .demo_inspectable import DemoInspectable
from .set_int_command import SetIntCommand
from .systems_demo_feature import SystemsDemoFeature
from .systems_specs import SYSTEMS_LIFECYCLE_SPEC, SYSTEMS_RUNTIME_SPEC, SYSTEMS_WINDOW_SPEC
from .systems_window_presenter import SystemsWindowPresenter

FEATURE_PACKAGE_INFO = {
    "feature_name": "systems",
    "scene_scope": "main",
    "layout_standard": "feature package with package-local specs, classes, and helpers",
}

__all__ = [
    "DemoInspectable",
    "FEATURE_PACKAGE_INFO",
    "SetIntCommand",
    "SYSTEMS_LIFECYCLE_SPEC",
    "SYSTEMS_RUNTIME_SPEC",
    "SYSTEMS_WINDOW_SPEC",
    "SystemsDemoFeature",
    "SystemsWindowPresenter",
]
