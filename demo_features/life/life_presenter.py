"""Window presenter for the Life demo feature."""

from __future__ import annotations

from pygame import Rect

from gui_do import (
	ButtonControl,
	CanvasControl,
	SliderControl,
	ToggleControl,
	centered_horizontal_strip_layout,
	inset_rect,
	split_slot_bounds,
)
from gui_do.controls.chrome.window_presenter import WindowPresenter

from .life_specs import (
	_LIFE_CANVAS_CONTROL_SPEC,
	_LIFE_CTRL_GAP,
	_LIFE_CTRL_H,
	_LIFE_CTRL_SPACING,
	_LIFE_PAD,
	_LIFE_STRIP_CONTROL_SPECS,
	_LIFE_ZOOM_SLIDER_SPEC,
)


class LifePresenter(WindowPresenter):
	"""Window presenter for the Conway's Game of Life window."""

	def __init__(self, feature, host):
		super().__init__(None)
		self.feature = feature
		self.host = host
		self.canvas = None
		self.reset_button = None
		self.toggle = None
		self.zoom_slider = None

	def on_create(self):
		content_rect = self.window.content_rect()
		padded = inset_rect(content_rect, padding_x=_LIFE_PAD, padding_y=_LIFE_PAD)
		left = padded.left
		top = padded.top
		width = padded.width
		height = padded.height

		ctrl_y = top + height - _LIFE_CTRL_H
		canvas_h = max(1, ctrl_y - _LIFE_CTRL_GAP - top)
		canvas_rect = Rect(left, top, width, canvas_h)
		self.canvas = self._add_presenter_control(
			CanvasControl(
				_LIFE_CANVAS_CONTROL_SPEC["control_id"],
				canvas_rect,
				max_events=int(_LIFE_CANVAS_CONTROL_SPEC["max_events"]),
			)
		)
		self.feature.canvas = self.canvas

		slots = centered_horizontal_strip_layout(
			left=left, width=width, y=ctrl_y, item_count=4, item_height=_LIFE_CTRL_H, spacing=_LIFE_CTRL_SPACING,
		)
		zoom_slider_slot_1, zoom_slider_slot_2 = slots[2], slots[3]

		for control_spec in _LIFE_STRIP_CONTROL_SPECS:
			self._build_strip_control_from_spec(control_spec, slots)

		slider_left, slider_right = split_slot_bounds([zoom_slider_slot_1, zoom_slider_slot_2])
		slider_height = int(_LIFE_ZOOM_SLIDER_SPEC["height"])
		slider_y = ctrl_y + max(0, (_LIFE_CTRL_H - slider_height) // 2)
		slider_rect = Rect(
			slider_left,
			slider_y,
			max(int(_LIFE_ZOOM_SLIDER_SPEC["min_width"]), slider_right - slider_left),
			slider_height,
		)
		on_change = getattr(self.feature, str(_LIFE_ZOOM_SLIDER_SPEC["on_change_attr"]))
		self.zoom_slider = self._add_presenter_control(
			SliderControl(
				str(_LIFE_ZOOM_SLIDER_SPEC["control_id"]),
				slider_rect,
				_LIFE_ZOOM_SLIDER_SPEC["axis"],
				float(_LIFE_ZOOM_SLIDER_SPEC["min"]),
				float(_LIFE_ZOOM_SLIDER_SPEC["max"]),
				float(_LIFE_ZOOM_SLIDER_SPEC["value"]),
				on_change=on_change,
			)
		)
		self.zoom_slider.set_accessibility(
			role=str(_LIFE_ZOOM_SLIDER_SPEC["accessibility_role"]),
			label=str(_LIFE_ZOOM_SLIDER_SPEC["accessibility_label"]),
		)
		self._bind_control_refs(_LIFE_ZOOM_SLIDER_SPEC, self.zoom_slider)

		self.feature.demo = self.host
		self.feature.window = self.window
		self.feature.life_origin = [self.canvas.rect.width / 2.0, self.canvas.rect.height / 2.0]
		self.feature.life_cell_size = 12
		self.feature.life_zoom_slider_last_value = int(round(self.zoom_slider.value))
		self.feature.life_dragging = False
		self.feature._send_life_logic_command("snapshot")
		self.window.visible = False

	def _add_presenter_control(self, control):
		self.add_control(control)
		return control

	def _build_strip_control_from_spec(self, control_spec, slots) -> None:
		slot_rect = Rect(slots[int(control_spec["slot_index"])])
		kind = str(control_spec["kind"])
		if kind == "button":
			handler = getattr(self.feature, str(control_spec["handler_attr"]))
			control = self._add_presenter_control(
				ButtonControl(
					str(control_spec["control_id"]),
					slot_rect,
					str(control_spec["label"]),
					handler,
					style=str(control_spec["style"]),
				)
			)
		elif kind == "toggle":
			control = self._add_presenter_control(
				ToggleControl(
					str(control_spec["control_id"]),
					slot_rect,
					str(control_spec["off_text"]),
					str(control_spec["on_text"]),
					pushed=bool(control_spec["pushed"]),
					style=str(control_spec["style"]),
				)
			)
		else:
			raise ValueError(f"Unsupported life strip control kind: {kind}")

		control.set_accessibility(
			role=str(control_spec["accessibility_role"]),
			label=str(control_spec["accessibility_label"]),
		)
		self._bind_control_refs(control_spec, control)

	def _bind_control_refs(self, control_spec, control) -> None:
		presenter_attr = control_spec.get("presenter_attr")
		feature_attr = control_spec.get("feature_attr")
		if presenter_attr:
			setattr(self, str(presenter_attr), control)
		if feature_attr:
			setattr(self.feature, str(feature_attr), control)

	def handle_event(self, event):
		return self._event_handler_impl(event)

	def before_update(self, dt_seconds: float):
		_ = dt_seconds
		self._preamble_impl()

	def after_update(self, dt_seconds: float):
		_ = dt_seconds
		self._postamble_impl()

	def _event_handler_impl(self, event):
		demo = self.host
		canvas = self.canvas
		window = self.window

		if event.is_mouse_down(3) and event.collides(canvas.rect):
			pos = event.pos
			if pos is not None:
				self.feature.life_dragging = True
				demo.app.set_cursor("hand")
				demo.app.set_lock_point(canvas, pos)
				return True

		if event.is_mouse_up(3):
			if self.feature.life_dragging:
				self.feature.life_dragging = False
				demo.app.set_cursor("normal")
				demo.app.set_lock_point(None)
				return True

		if event.is_mouse_motion() and self.feature.life_dragging:
			delta = demo.app.get_lock_point_motion_delta(event)
			if delta is None:
				rel = event.rel
				delta = (rel[0], rel[1]) if isinstance(rel, tuple) and len(rel) == 2 else (0, 0)
			self.feature.life_origin[0] -= delta[0]
			self.feature.life_origin[1] -= delta[1]
			return True

		if event.is_mouse_wheel():
			locked = getattr(demo.app, "mouse_point_locked", False)
			lock_pos = getattr(demo.app, "lock_point_pos", None)
			pointer_pos = lock_pos if locked and lock_pos is not None else event.pos
			if pointer_pos is not None and canvas.rect.collidepoint(pointer_pos):
				if locked and lock_pos is not None:
					lp = demo.app.convert_to_window(lock_pos, window)
					anchor_local = (lp[0] - (canvas.rect.left - window.rect.left), lp[1] - (canvas.rect.top - window.rect.top))
				else:
					anchor_local = (pointer_pos[0] - canvas.rect.left, pointer_pos[1] - canvas.rect.top)
				self.feature.zoom_life_view_about(anchor_local, self.feature.life_cell_size - (event.wheel_delta * 2))
				return True

		return False

	def _preamble_impl(self):
		slider_value = max(0, min(11, int(round(self.zoom_slider.value))))
		self.feature.sync_life_zoom_from_slider(slider_value)

	def _postamble_impl(self):
		self._update_life()

	def _update_life(self):
		self.feature._update_life_frame_core(self.host, self.canvas, self.toggle)


__all__ = ["LifePresenter"]
