"""Logic companion for the Mandelbrot demo feature."""

from __future__ import annotations

from typing import Tuple

from pygame import Rect
from gui_do import LogicFeature


class MandelbrotLogicFeature(LogicFeature):
	"""Domain logic provider for Mandelbrot pixel and algorithm calculations."""

	RECURSIVE_LEAF_SPAN = 8

	def __init__(self, name: str = "mandelbrot_logic_primary", *, scene_name: str = "main") -> None:
		super().__init__(name, scene_name=scene_name)
		self.mandel_cols = (
			(66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
			(0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
			(134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
			(255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3),
		)
		self.max_iter = 48

	def bind_runtime(self, _host) -> None:
		self._feature_manager.register_runnable(self.name, "iterative_task", self.run_iterative_task)
		self._feature_manager.register_runnable(self.name, "recursive_task", self.run_recursive_task)

	def mandel_col(self, k: int) -> Tuple[int, int, int]:
		if k >= self.max_iter - 1:
			return (0, 0, 0)
		return self.mandel_cols[k % len(self.mandel_cols)]

	@staticmethod
	def mandel_viewport(width: int, height: int) -> Tuple[complex, float]:
		center = -0.7 + 0.0j
		extent = 2.5 + 2.5j
		scale = max((extent / width).real, (extent / height).imag)
		return center, scale

	def mandel_pixel(self, px: int, py: int, width: int, height: int, center: complex, scale: float) -> int:
		c = center + (px - width // 2 + (py - height // 2) * 1j) * scale
		z = 0j
		for k in range(self.max_iter):
			z = z * z + c
			if (z * z.conjugate()).real > 4.0:
				return k
		return self.max_iter - 1

	def run_iterative_task(self, scheduler, task_id, params):
		width, height = params["size"]
		center = params["center"]
		scale = params["scale"]
		for y in range(height):
			row = [self.mandel_pixel(x, y, width, height, center, scale) for x in range(width)]
			scheduler.send_message(task_id, (y, row))
		return None

	def _recursive_fill(self, scheduler, task_id: str, x: int, y: int, w: int, h: int, width: int, height: int, center: complex, scale: float) -> None:
		if w <= 0 or h <= 0:
			return
		if w <= self.RECURSIVE_LEAF_SPAN or h <= self.RECURSIVE_LEAF_SPAN:
			values = []
			for yy in range(y, y + h):
				for xx in range(x, x + w):
					values.append(self.mandel_pixel(xx, yy, width, height, center, scale))
			scheduler.send_message(task_id, (x, y, w, h, values))
			return
		hw = w // 2
		hh = h // 2
		self._recursive_fill(scheduler, task_id, x, y, hw, hh, width, height, center, scale)
		self._recursive_fill(scheduler, task_id, x + hw, y, w - hw, hh, width, height, center, scale)
		self._recursive_fill(scheduler, task_id, x, y + hh, hw, h - hh, width, height, center, scale)
		self._recursive_fill(scheduler, task_id, x + hw, y + hh, w - hw, h - hh, width, height, center, scale)

	def run_recursive_task(self, scheduler, task_id, params):
		width, height = params["size"]
		center = params["center"]
		scale = params["scale"]
		rect = Rect(params.get("rect", Rect(0, 0, width, height)))
		self._recursive_fill(scheduler, task_id, rect.x, rect.y, rect.width, rect.height, width, height, center, scale)
		return None


__all__ = ["MandelbrotLogicFeature"]
