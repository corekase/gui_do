"""Layout constants and status event kind constants for the Mandelbrot demo feature."""

from __future__ import annotations

from gui_do.features.data_driven_runtime import (
    AnchoredWindowSpec,
    LogicBindingSpec,
    RoutedFeatureLifecycleSpec,
)

from .mandelbrot_logic_feature import MandelbrotLogicFeature

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
_PAD = 10
_CANVAS_H = 560
_BTN_W, _BTN_H, _BTN_GAP = 120, 30, 8
_SPLIT_GAP = 6
_ROW_PAD = 12
_STATUS_H = 20
_NUM_BTNS = 5   # Reset + four launch buttons
_CANVAS_W = _NUM_BTNS * _BTN_W + (_NUM_BTNS - 1) * _BTN_GAP + 2 * _ROW_PAD
_TITLEBAR_H = 24
_WINDOW_SIZE = (
    _PAD + _CANVAS_W + _PAD,
    _TITLEBAR_H + _PAD + _CANVAS_H + 8 + _BTN_H + 6 + _STATUS_H + _PAD,
)

# ---------------------------------------------------------------------------
# Status event kind constants
# ---------------------------------------------------------------------------
MANDEL_STATUS_TOPIC = "demo.mandel.status"
MANDEL_STATUS_SCOPE = "main"
MANDEL_KIND_IDLE = "idle"
MANDEL_KIND_CLEARED = "cleared"
MANDEL_KIND_RUNNING_ITERATIVE = "running_iterative"
MANDEL_KIND_RUNNING_RECURSIVE = "running_recursive"
MANDEL_KIND_RUNNING_ONE_SPLIT = "running_one_split"
MANDEL_KIND_RUNNING_FOUR_SPLIT = "running_four_split"
MANDEL_KIND_FAILED = "failed"
MANDEL_KIND_COMPLETE = "complete"
MANDEL_KIND_STATUS = "status"

_STATUS_TEXT = {
    MANDEL_KIND_IDLE:               "Mandelbrot: idle",
    MANDEL_KIND_CLEARED:            "Mandelbrot: cleared",
    MANDEL_KIND_RUNNING_ITERATIVE:  "Mandelbrot: running iterative",
    MANDEL_KIND_RUNNING_RECURSIVE:  "Mandelbrot: running recursive",
    MANDEL_KIND_RUNNING_ONE_SPLIT:  "Mandelbrot: running 1M 4Tasks",
    MANDEL_KIND_RUNNING_FOUR_SPLIT: "Mandelbrot: running 4M 4Tasks",
    MANDEL_KIND_COMPLETE:           "Mandelbrot: complete",
}

MANDEL_LOGIC_PRIMARY = "mandelbrot_logic_primary"
MANDEL_LOGIC_SPLITS = (
    "mandelbrot_logic_can1",
    "mandelbrot_logic_can2",
    "mandelbrot_logic_can3",
    "mandelbrot_logic_can4",
)
MANDEL_SPLIT_KEYS = ("Canvas 1", "Canvas 2", "Canvas 3", "Canvas 4")
MANDEL_ALL_TASK_IDS = ("Iterative", "Recursive", "Task 1", "Task 2", "Task 3", "Task 4") + MANDEL_SPLIT_KEYS
MANDEL_TASK_ID_ITERATIVE = MANDEL_ALL_TASK_IDS[0]
MANDEL_TASK_ID_RECURSIVE = MANDEL_ALL_TASK_IDS[1]
MANDEL_TASK_IDS_QUADRANTS = MANDEL_ALL_TASK_IDS[2:6]

MANDEL_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="mandelbrot_window",
    title="Mandelbrot",
    size=_WINDOW_SIZE,
    anchor="top_left",
    margin=(28, 92),
    use_frame_backdrop=True,
)

MANDEL_LOGIC_BINDINGS = (
    LogicBindingSpec(alias="primary", provider_name=MANDEL_LOGIC_PRIMARY),
    LogicBindingSpec(alias=MANDEL_SPLIT_KEYS[0], provider_name=MANDEL_LOGIC_SPLITS[0]),
    LogicBindingSpec(alias=MANDEL_SPLIT_KEYS[1], provider_name=MANDEL_LOGIC_SPLITS[1]),
    LogicBindingSpec(alias=MANDEL_SPLIT_KEYS[2], provider_name=MANDEL_LOGIC_SPLITS[2]),
    LogicBindingSpec(alias=MANDEL_SPLIT_KEYS[3], provider_name=MANDEL_LOGIC_SPLITS[3]),
)


def build_mandel_lifecycle_spec(runtime_spec_factory) -> RoutedFeatureLifecycleSpec:
    return RoutedFeatureLifecycleSpec(
        companion_providers=(
            lambda: MandelbrotLogicFeature(MANDEL_LOGIC_PRIMARY),
            lambda: MandelbrotLogicFeature(MANDEL_LOGIC_SPLITS[0]),
            lambda: MandelbrotLogicFeature(MANDEL_LOGIC_SPLITS[1]),
            lambda: MandelbrotLogicFeature(MANDEL_LOGIC_SPLITS[2]),
            lambda: MandelbrotLogicFeature(MANDEL_LOGIC_SPLITS[3]),
        ),
        runtime_spec_factory=runtime_spec_factory,
        runtime_spec_attr_name="_runtime_spec",
        scheduler_attr_name="scheduler",
    )

__all__ = [
    "MANDEL_ALL_TASK_IDS",
    "MANDEL_STATUS_TOPIC",
    "MANDEL_STATUS_SCOPE",
    "MANDEL_LOGIC_BINDINGS",
    "MANDEL_LOGIC_PRIMARY",
    "MANDEL_LOGIC_SPLITS",
    "MANDEL_SPLIT_KEYS",
    "MANDEL_TASK_IDS_QUADRANTS",
    "MANDEL_TASK_ID_ITERATIVE",
    "MANDEL_TASK_ID_RECURSIVE",
    "MANDEL_WINDOW_SPEC",
    "MANDEL_KIND_IDLE",
    "MANDEL_KIND_CLEARED",
    "MANDEL_KIND_RUNNING_ITERATIVE",
    "MANDEL_KIND_RUNNING_RECURSIVE",
    "MANDEL_KIND_RUNNING_ONE_SPLIT",
    "MANDEL_KIND_RUNNING_FOUR_SPLIT",
    "MANDEL_KIND_FAILED",
    "MANDEL_KIND_COMPLETE",
    "MANDEL_KIND_STATUS",
    "build_mandel_lifecycle_spec",
]
