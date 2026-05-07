"""Layout constants and status event kind constants for the Mandelbrot demo feature."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
_PAD = 10
_CANVAS_H = 560
_BTN_W, _BTN_H, _BTN_GAP = 120, 30, 8
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
