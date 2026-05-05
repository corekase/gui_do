"""Mandelbrot demo feature package.

This package is the canonical container for Mandelbrot feature behavior and specs.
"""

from .mandelbrot_status_event import MandelStatusEvent
from .mandelbrot_logic import MandelbrotLogicFeature
from .mandelbrot_feature import MandelbrotFeature
from .mandelbrot_specs import (
    MANDEL_KIND_CLEARED,
    MANDEL_KIND_COMPLETE,
    MANDEL_KIND_FAILED,
    MANDEL_KIND_IDLE,
    MANDEL_KIND_RUNNING_FOUR_SPLIT,
    MANDEL_KIND_RUNNING_ITERATIVE,
    MANDEL_KIND_RUNNING_ONE_SPLIT,
    MANDEL_KIND_RUNNING_RECURSIVE,
    MANDEL_KIND_STATUS,
    MANDEL_STATUS_SCOPE,
    MANDEL_STATUS_TOPIC,
)
from .mandelbrot_presenter import MandelbrotPresenter

FEATURE_PACKAGE_INFO = {
    "feature_name": "mandelbrot",
    "scene_scope": "main",
    "layout_standard": "feature package with package-local specs and class modules",
}

__all__ = [
    "FEATURE_PACKAGE_INFO",
    "MANDEL_KIND_CLEARED",
    "MANDEL_KIND_COMPLETE",
    "MANDEL_KIND_FAILED",
    "MANDEL_KIND_IDLE",
    "MANDEL_KIND_RUNNING_FOUR_SPLIT",
    "MANDEL_KIND_RUNNING_ITERATIVE",
    "MANDEL_KIND_RUNNING_ONE_SPLIT",
    "MANDEL_KIND_RUNNING_RECURSIVE",
    "MANDEL_KIND_STATUS",
    "MANDEL_STATUS_SCOPE",
    "MANDEL_STATUS_TOPIC",
    "MandelStatusEvent",
    "MandelbrotLogicFeature",
    "MandelbrotFeature",
    "MandelbrotPresenter",
]
