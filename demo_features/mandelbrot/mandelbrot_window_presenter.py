"""Window presenter for the Mandelbrot demo feature."""

from __future__ import annotations

from pygame import Rect

from gui_do import ButtonControl, CanvasControl, LabelControl, centered_horizontal_strip_layout, inset_rect
from gui_do.controls.chrome.window_presenter import WindowPresenter

from .mandelbrot_render_feature import (
	_MANDEL_BTN_COUNT,
	_MANDEL_BTN_SPACING,
	_MANDEL_CANVAS_H,
	_MANDEL_CANVAS_W,
	_MANDEL_CTRL_GAP,
	_MANDEL_CTRL_H,
	_MANDEL_PAD,
	_MANDEL_PRIMARY_CANVAS_SPEC,
	_MANDEL_RESET_BUTTON_SPEC,
	_MANDEL_ROW_STRIP_PAD,
	_MANDEL_SPLIT_CANVAS_SPECS,
	_MANDEL_STATUS_GAP,
	_MANDEL_STATUS_H,
	_MANDEL_STATUS_LABEL_SPEC,
	_MANDEL_TASK_BUTTON_SPECS,
)


class MandelbrotWindowPresenter(WindowPresenter):
	"""Window presenter for the Mandelbrot demo window."""

	def __init__(self, feature, host):
		super().__init__(None)
		self.feature = feature
		self.host = host
		self.primary_canvas = None
		self.split_canvases = {}
		self.reset_button = None
		self.mandel_iter_button = None
		self.mandel_recur_button = None
		self.mandel_one_split_button = None
		self.mandel_four_split_button = None
		self.status_label = None

	def on_create(self):
		from gui_do import partition_rects
		content_rect = self.window.content_rect()
		padded = inset_rect(content_rect, padding_x=_MANDEL_PAD, padding_y=_MANDEL_PAD)

		canvas_area = Rect(padded.left, padded.top, _MANDEL_CANVAS_W, _MANDEL_CANVAS_H)

		self.primary_canvas = self._add_control(
			CanvasControl(
				str(_MANDEL_PRIMARY_CANVAS_SPEC["control_id"]),
				Rect(canvas_area),
				max_events=int(_MANDEL_PRIMARY_CANVAS_SPEC["max_events"]),
			)
		)
		self.feature.primary_canvas = self.primary_canvas

		self.split_canvases = self._build_split_canvases(canvas_area, partition_rects)
		self._register_split_canvases(self.split_canvases)
		self.feature.split_canvases = self.split_canvases

		controls_y = padded.top + _MANDEL_CANVAS_H + _MANDEL_CTRL_GAP
		slots = centered_horizontal_strip_layout(
			left=padded.left + _MANDEL_ROW_STRIP_PAD,
			width=max(1, _MANDEL_CANVAS_W - 2 * _MANDEL_ROW_STRIP_PAD),
			y=controls_y, item_count=_MANDEL_BTN_COUNT, item_height=_MANDEL_CTRL_H, spacing=_MANDEL_BTN_SPACING,
		)
		reset_slot = slots[int(_MANDEL_RESET_BUTTON_SPEC["slot_index"])]
		self.reset_button = self._add_button_control(
			str(_MANDEL_RESET_BUTTON_SPEC["control_id"]),
			reset_slot,
			str(_MANDEL_RESET_BUTTON_SPEC["label"]),
			lambda: self.feature.clear(self.host),
			style=str(_MANDEL_RESET_BUTTON_SPEC["style"]),
		)
		self.reset_button.set_accessibility(
			role=str(_MANDEL_RESET_BUTTON_SPEC["accessibility_role"]),
			label=str(_MANDEL_RESET_BUTTON_SPEC["accessibility_label"]),
		)
		self.feature.reset_button = self.reset_button

		task_buttons = self._build_task_buttons(slots[1:])

		(
			self.mandel_iter_button,
			self.mandel_recur_button,
			self.mandel_one_split_button,
			self.mandel_four_split_button,
		) = tuple(task_buttons)
		self.feature.task_buttons = tuple(task_buttons)

		status_y = controls_y + _MANDEL_CTRL_H + _MANDEL_STATUS_GAP
		self.status_label = self._add_label_control(
			str(_MANDEL_STATUS_LABEL_SPEC["control_id"]),
			Rect(padded.left, status_y, _MANDEL_CANVAS_W, _MANDEL_STATUS_H),
			self.feature.status_text,
		)
		self.feature.status_label = self.status_label

		self.feature.demo = self.host
		self.feature.window = self.window
		self.feature.menu_bar = None
		self.feature.set_task_buttons_disabled(self.host, False)
		self.feature.clear(self.host)
		self.window.visible = False

	def _build_split_canvases(self, canvas_area: Rect, partition_rects):
		"""Build the four split Mandelbrot canvases mapped by declarative keys."""
		canvas_rects = partition_rects(canvas_area, rows=2, cols=2, gap=6)
		return {
			canvas_key: CanvasControl(canvas_key, canvas_rects[index], max_events=max_events)
			for index, (canvas_key, max_events) in enumerate(_MANDEL_SPLIT_CANVAS_SPECS)
		}

	def _register_split_canvases(self, split_canvases) -> None:
		"""Register split canvases as hidden controls until split mode is activated."""
		for canvas in split_canvases.values():
			canvas.visible = False
			self.add_control(canvas)

	def _add_control(self, control):
		"""Add a presenter-managed control and return it."""
		self.add_control(control)
		return control

	def _add_button_control(self, control_id: str, rect: Rect, text: str, on_click, *, style: str):
		"""Create and register a ButtonControl in one call."""
		return self._add_control(ButtonControl(control_id, Rect(rect), text, on_click, style=style))

	def _add_label_control(self, control_id: str, rect: Rect, text: str):
		"""Create and register a LabelControl in one call."""
		return self._add_control(LabelControl(control_id, Rect(rect), text))

	def _build_task_buttons(self, task_slots):
		"""Build task launch buttons from declarative specs."""
		task_buttons = []
		for slot_rect, (control_id, label, launch_method_name, style, accessibility_label) in zip(
			task_slots,
			_MANDEL_TASK_BUTTON_SPECS,
		):
			launch_method = getattr(self.feature, launch_method_name)
			button = self._add_button_control(
				control_id,
				slot_rect,
				label,
				lambda _method=launch_method: _method(self.host),
				style=style,
			)
			button.set_accessibility(role="button", label=accessibility_label)
			task_buttons.append(button)
		return tuple(task_buttons)


__all__ = ["MandelbrotWindowPresenter"]
