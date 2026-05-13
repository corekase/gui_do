"""Shared specs and layout constants for the Life demo feature."""

from __future__ import annotations

from gui_do import LayoutAxis
from gui_do.features.data_driven_runtime import (
    AnchoredWindowSpec,
    LogicBindingSpec,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
)
from .life_logic_feature import LifeLogicFeature


# ---------------------------------------------------------------------------
# Life window layout constants — single source of truth for sizing and layout
# ---------------------------------------------------------------------------
_LIFE_PAD = 10           # Uniform padding inside the window body on all four sides
_LIFE_CTRL_GAP = 8       # Gap between the canvas bottom edge and the control strip
_LIFE_CTRL_H = 28        # Control strip height
_LIFE_CTRL_SPACING = 12  # Horizontal spacing between items in the control strip
_LIFE_CANVAS_SIZE = 600  # Square canvas dimension
_LIFE_TITLEBAR_H = 24    # Estimated titlebar height (matches size-14 title font)

_LIFE_BODY_W = _LIFE_PAD + _LIFE_CANVAS_SIZE + _LIFE_PAD
_LIFE_BODY_H = (
    _LIFE_PAD + _LIFE_CANVAS_SIZE + _LIFE_CTRL_GAP + _LIFE_CTRL_H + _LIFE_PAD
)
_LIFE_WINDOW_SIZE = (_LIFE_BODY_W, _LIFE_TITLEBAR_H + _LIFE_BODY_H)

_LIFE_CANVAS_CONTROL_SPEC = {
    "control_id": "life_canvas",
    "max_events": 256,
}

_LIFE_STRIP_CONTROL_SPECS = (
    {
        "kind": "button",
        "slot_index": 0,
        "presenter_attr": "reset_button",
        "feature_attr": "reset_button",
        "control_id": "life_reset",
        "label": "Reset",
        "style": "angle",
        "handler_attr": "life_reset",
        "accessibility_role": "button",
        "accessibility_label": "Reset life board",
    },
    {
        "kind": "toggle",
        "slot_index": 1,
        "presenter_attr": "toggle",
        "feature_attr": "toggle",
        "control_id": "life_toggle",
        "off_text": "Stop",
        "on_text": "Start",
        "pushed": False,
        "style": "round",
        "accessibility_role": "toggle",
        "accessibility_label": "Run life simulation",
    },
)

_LIFE_ZOOM_SLIDER_SPEC = {
    "control_id": "life_zoom",
    "axis": LayoutAxis.HORIZONTAL,
    "min": 0.0,
    "max": 11.0,
    "value": 5.0,
    "height": 20,
    "min_width": 80,
    "presenter_attr": "zoom_slider",
    "feature_attr": "zoom_slider",
    "on_change_attr": "on_life_zoom_slider_changed",
    "accessibility_role": "slider",
    "accessibility_label": "Life zoom",
}
# ---------------------------------------------------------------------------

_LIFE_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="life_window",
    title="Conway's Game of Life",
    size=_LIFE_WINDOW_SIZE,
    anchor="top_right",
    margin=(28, 92),
    use_frame_backdrop=True,
)

_LIFE_LOGIC_BINDINGS = (
    LogicBindingSpec(alias="life", provider_name="life_simulation_logic"),
)

_LIFE_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    scheduler_attr_name="scheduler",
    scheduler_dispatch_limit=512,
    logic_bindings=_LIFE_LOGIC_BINDINGS,
)

_LIFE_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    companion_providers=(lambda: LifeLogicFeature(),),
    runtime_spec=_LIFE_RUNTIME_SPEC,
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)

LIFE_LOGIC_TOPIC = "life_logic"
LIFE_EVENT_STATE = "state"
LIFE_KEY_TOPIC = "topic"
LIFE_KEY_EVENT = "event"
LIFE_KEY_COMMAND = "command"
LIFE_KEY_CELLS = "life_cells"


__all__ = [
    "LIFE_EVENT_STATE",
    "LIFE_KEY_CELLS",
    "LIFE_KEY_COMMAND",
    "LIFE_KEY_EVENT",
    "LIFE_KEY_TOPIC",
    "LIFE_LOGIC_TOPIC",
    "_LIFE_LIFECYCLE_SPEC",
    "_LIFE_WINDOW_SPEC",
]
