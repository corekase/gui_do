"""Shared specs and status constants for the Mandelbrot demo feature."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Mandelbrot window layout constants – single source of truth for sizing and layout
# ---------------------------------------------------------------------------
_MANDEL_PAD = 10            # Uniform padding inside the window body on all four sides
_MANDEL_CTRL_GAP = 8        # Gap between canvas bottom edge and the button strip
_MANDEL_STATUS_GAP = 6      # Gap between button strip and status label
_MANDEL_CTRL_H = 30         # Button strip height
_MANDEL_STATUS_H = 20       # Status label height
_MANDEL_CANVAS_H = 560      # Canvas height

# Button strip sizing – canvas width is derived so buttons always fit exactly
_MANDEL_BTN_COUNT = 5
_MANDEL_BTN_W = 120         # Per-button width (change this to resize all buttons)
_MANDEL_BTN_SPACING = 8     # Gap between adjacent buttons
_MANDEL_ROW_STRIP_PAD = 12  # Padding on each side of the button row
_MANDEL_CANVAS_W = (
    _MANDEL_BTN_COUNT * _MANDEL_BTN_W
    + (_MANDEL_BTN_COUNT - 1) * _MANDEL_BTN_SPACING
    + 2 * _MANDEL_ROW_STRIP_PAD
)

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

__all__ = [
    "MANDEL_STATUS_TOPIC",
    "MANDEL_STATUS_SCOPE",
    "MANDEL_KIND_IDLE",
    "MANDEL_KIND_CLEARED",
    "MANDEL_KIND_RUNNING_ITERATIVE",
    "MANDEL_KIND_RUNNING_RECURSIVE",
    "MANDEL_KIND_RUNNING_ONE_SPLIT",
    "MANDEL_KIND_RUNNING_FOUR_SPLIT",
    "MANDEL_KIND_FAILED",
    "MANDEL_KIND_COMPLETE",
    "MANDEL_KIND_STATUS",
]

_MANDEL_SPLIT_CANVAS_SPECS = (
    ("can1", 32),
    ("can2", 32),
    ("can3", 32),
    ("can4", 32),
)
_MANDEL_TASK_BUTTON_SPECS = (
    ("mandel_iter", "Iterative", "launch_iterative", "round", "Run Mandelbrot iterative"),
    ("mandel_recur", "Recursive", "launch_recursive", "round", "Run Mandelbrot recursive"),
    ("mandel_one_split", "1M 4Tasks", "launch_one_split", "round", "Run Mandelbrot one canvas split"),
    ("mandel_four_split", "4M 4Tasks", "launch_four_split", "round", "Run Mandelbrot four canvases split"),
)
_MANDEL_PRIMARY_CANVAS_SPEC = {
    "control_id": "mandel_canvas",
    "max_events": 128,
}
_MANDEL_RESET_BUTTON_SPEC = {
    "control_id": "mandel_reset",
    "label": "Reset",
    "style": "angle",
    "slot_index": 0,
    "accessibility_role": "button",
    "accessibility_label": "Clear Mandelbrot surfaces",
}
_MANDEL_STATUS_LABEL_SPEC = {
    "control_id": "mandel_status",
}
