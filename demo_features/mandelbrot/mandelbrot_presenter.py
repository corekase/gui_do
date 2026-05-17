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



# --- Refactored: Use gui_do presenter control builder and layout helpers ---
from gui_do.features.presenter_control_builders import ControlFactory, PanelPresenterMixin
from gui_do.features.layout_geometry import VerticalGridSequencePlacer

class MandelbrotPresenter(WindowPresenter, PanelPresenterMixin):
    """Constructs the Mandelbrot window controls and wires them to the feature."""

    def __init__(self, feature, host) -> None:
        super().__init__(None)
        self.feature = feature
        self.host = host

    def on_create(self) -> None:
        feature = self.feature
        host = self.host
        content_rect = self.window.content_rect()

        canvas_y = content_rect.top + _PAD
        buttons_y = canvas_y + _CANVAS_H + 9
        status_y = buttons_y + _BTN_H + 6

        # Canvas controls
        feature.primary_canvas = self.add_control(CanvasControl("mandel_canvas", Rect(content_rect.left + _PAD, canvas_y, _CANVAS_W, _CANVAS_H), max_events=128))
        feature.split_canvases = {}
        placer = VerticalGridSequencePlacer(2, (_CANVAS_W // 2 - _SPLIT_GAP, _CANVAS_H // 2 - _SPLIT_GAP), padding=_SPLIT_GAP)
        for key in MANDEL_SPLIT_KEYS:
            x, y = placer.next()
            canvas = CanvasControl(key, Rect(content_rect.left + _PAD + x, canvas_y + y, _CANVAS_W // 2 - _SPLIT_GAP, _CANVAS_H // 2 - _SPLIT_GAP), max_events=32)
            canvas.visible = False
            self.add_control(canvas)
            feature.split_canvases[key] = canvas

        # Button row
        btn_defs = [
            {"type": "button", "id": "mandel_reset", "label": "Reset", "rect": Rect(content_rect.left + _ROW_PAD, buttons_y, 120, _BTN_H), "callback": lambda: feature.clear(host), "style": "angle", "accessibility": ("button", "Clear Mandelbrot surfaces")},
            {"type": "button", "id": "mandel_iter", "label": "Iterative", "rect": Rect(0, 0, 120, _BTN_H), "callback": lambda: feature.launch_iterative(host), "style": "round", "accessibility": ("button", "Run iterative")},
            {"type": "button", "id": "mandel_recur", "label": "Recursive", "rect": Rect(0, 0, 120, _BTN_H), "callback": lambda: feature.launch_recursive(host), "style": "round", "accessibility": ("button", "Run recursive")},
            {"type": "button", "id": "mandel_one_split", "label": "1M 4Tasks", "rect": Rect(0, 0, 120, _BTN_H), "callback": lambda: feature.launch_one_split(host), "style": "round", "accessibility": ("button", "Run 1-canvas 4-task split")},
            {"type": "button", "id": "mandel_four_split", "label": "4M 4Tasks", "rect": Rect(0, 0, 120, _BTN_H), "callback": lambda: feature.launch_four_split(host), "style": "round", "accessibility": ("button", "Run 4-canvas 4-task split")},
        ]
        factory = ControlFactory({
            "button": lambda id, label, rect, callback, style, accessibility: self._add_btn(id, label, rect, callback, style, accessibility)
        })
        feature.reset_button = factory.create(btn_defs[0])
        feature.task_buttons = tuple(factory.create(spec) for spec in btn_defs[1:])

        # Place buttons in a row
        btn_x = content_rect.left + _ROW_PAD
        for i, btn in enumerate((feature.reset_button,) + feature.task_buttons):
            btn.rect = Rect(btn_x + i * (120 + _BTN_GAP), buttons_y, 120, _BTN_H)

        # Status label
        feature.status_label = self.add_control(LabelControl(
            "mandel_status",
            Rect(content_rect.left + _PAD, status_y, _CANVAS_W, _STATUS_H),
            feature.status_text,
        ))

        feature.window = self.window
        feature.demo = host
        feature.clear(host)
        self.window.visible = False

    def _add_btn(self, id, label, rect, callback, style, accessibility):
        btn = ButtonControl(id, rect, label, callback, style=style)
        role, acc_label = accessibility
        btn.set_accessibility(role=role, label=acc_label)
        self.add_control(btn)
        return btn


__all__ = [
    "MandelbrotPresenter",
]
