"""Controls showcase demo feature package.

This package owns the showcase feature, its specs, and feature-local support classes.
"""

from .control_gallery_layout_manager import ControlGalleryLayoutManager
from .controls_showcase_feature import ControlsShowcaseFeature
from .controls_specs import BASICS_SUPPRESSED_LABEL_NAMES, CONTROLS_RUNTIME_SPEC
from .showcase_inspectable import ShowcaseInspectable

FEATURE_PACKAGE_INFO = {
    "feature_name": "controls",
    "scene_scope": "control_showcase",
    "layout_standard": "feature package with package-local specs, classes, and helpers",
}

__all__ = [
    "BASICS_SUPPRESSED_LABEL_NAMES",
    "CONTROLS_RUNTIME_SPEC",
    "ControlGalleryLayoutManager",
    "ControlsShowcaseFeature",
    "FEATURE_PACKAGE_INFO",
    "ShowcaseInspectable",
]
