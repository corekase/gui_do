"""Window presenter for Mandelbrot demo controls."""

from __future__ import annotations

from pygame import Rect

from gui_do import ButtonControl, CanvasControl, LabelControl
from gui_do.controls.chrome.window_presenter import WindowPresenter

from .mandelbrot_specs import (
    _BTN_GAP,
    _BTN_H,
    _CANVAS_H,
    _CANVAS_W,
    _PAD,
    _ROW_PAD,
    _SPLIT_GAP,
    _STATUS_H,
    MANDEL_SPLIT_KEYS,
)


class MandelbrotPresenter(WindowPresenter):
    """Constructs the Mandelbrot window controls and wires them to the feature."""

    def __init__(self, feature, host) -> None:
        super().__init__(None)
        self.feature = feature
        self.host = host

    def on_create(self) -> None:
        from gui_do import FlexLayout, GridLayout, GridPlacement

        feature = self.feature
        host = self.host
        content_rect = self.window.content_rect()
        inner_rect = Rect(
            content_rect.left + _PAD,
            content_rect.top + _PAD,
            max(1, content_rect.width - _PAD * 2),
            max(1, content_rect.height - _PAD * 2),
        )

        primary_canvas = CanvasControl("mandel_canvas", Rect(0, 0, _CANVAS_W, _CANVAS_H), max_events=128)
        feature.primary_canvas = self._add(primary_canvas)
        canvas_rect = Rect(inner_rect.left, inner_rect.top, _CANVAS_W, _CANVAS_H)
        primary_canvas.rect = Rect(canvas_rect)

        split_gap = _SPLIT_GAP
        split_canvas_w = max(1, (_CANVAS_W - split_gap) // 2)
        split_canvas_h = max(1, (_CANVAS_H - split_gap) // 2)
        split_grid = GridLayout(
            row_tracks=[split_canvas_h, split_canvas_h],
            col_tracks=[split_canvas_w, split_canvas_w],
            gap=split_gap,
            padding=0,
        )
        feature.split_canvases = {}
        for idx, key in enumerate(MANDEL_SPLIT_KEYS):
            row = idx // 2
            col = idx % 2
            canvas = CanvasControl(key, Rect(0, 0, split_canvas_w, split_canvas_h), max_events=32)
            canvas.visible = False
            split_grid.place(canvas, GridPlacement(row=row, col=col))
            self.add_control(canvas)
            feature.split_canvases[key] = canvas
        split_grid.apply(canvas_rect)

        btn_row = FlexLayout(direction="row", gap=_BTN_GAP, padding=0)
        feature.reset_button = self._add(ButtonControl(
            "mandel_reset", Rect(0, 0, 120, _BTN_H), "Reset", lambda: feature.clear(host), style="angle",
        ))
        feature.reset_button.set_accessibility(role="button", label="Clear Mandelbrot surfaces")
        btn_row.add(feature.reset_button, grow=0)

        task_defs = (
            ("mandel_iter", "Iterative", feature.launch_iterative, "Run iterative"),
            ("mandel_recur", "Recursive", feature.launch_recursive, "Run recursive"),
            ("mandel_one_split", "1M 4Tasks", feature.launch_one_split, "Run 1-canvas 4-task split"),
            ("mandel_four_split", "4M 4Tasks", feature.launch_four_split, "Run 4-canvas 4-task split"),
        )
        feature.task_buttons = tuple(
            self._make_task_btn(cid, label, method, tip, Rect(0, 0, 120, _BTN_H))
            for (cid, label, method, tip) in task_defs
        )
        for btn in feature.task_buttons:
            btn_row.add(btn, grow=0)
        btn_row_rect = Rect(
            inner_rect.left + _ROW_PAD,
            canvas_rect.bottom + 9,
            max(1, _CANVAS_W - (_ROW_PAD * 2)),
            _BTN_H,
        )
        btn_row.apply(btn_row_rect)

        feature.status_label = self._add(LabelControl(
            "mandel_status",
            Rect(0, 0, _CANVAS_W, _STATUS_H),
            feature.status_text,
        ))
        feature.status_label.rect = Rect(inner_rect.left, btn_row_rect.bottom + 9, _CANVAS_W, _STATUS_H)

        feature.window = self.window
        feature.demo = host
        feature.clear(host)
        self.window.visible = False

    def _add(self, control):
        self.add_control(control)
        return control

    def _make_task_btn(self, cid, label, method, tip, rect):
        btn = self._add(ButtonControl(cid, rect, label, lambda m=method: m(self.host), style="round"))
        btn.set_accessibility(role="button", label=tip)
        return btn


__all__ = [
    "MandelbrotPresenter",
]
