"""Life demo feature package.

This package is the canonical container for the Game of Life feature.
"""

from .life_simulation_feature import LifeSimulationFeature
from .life_simulation_logic_feature import LifeSimulationLogicFeature
from .life_specs import LIFE_LIFECYCLE_SPEC, LIFE_RUNTIME_SPEC, LIFE_WINDOW_SPEC
from .life_window_presenter import LifeWindowPresenter

FEATURE_PACKAGE_INFO = {
    "feature_name": "life",
    "scene_scope": "main",
    "layout_standard": "feature package with package-local specs and class modules",
}

__all__ = [
    "FEATURE_PACKAGE_INFO",
    "LIFE_LIFECYCLE_SPEC",
    "LIFE_RUNTIME_SPEC",
    "LIFE_WINDOW_SPEC",
    "LifeSimulationFeature",
    "LifeSimulationLogicFeature",
    "LifeWindowPresenter",
]
