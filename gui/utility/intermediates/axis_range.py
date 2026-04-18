from __future__ import annotations

from pygame import Rect

from ..events import GuiError, Orientation


class AxisRangeMixin:
    """Shared axis-orientation and pixel/logical conversion helpers."""

    _horizontal: Orientation
    _graphic_rect: Rect

    def _set_orientation(self, orientation: Orientation) -> None:
        """Set and validate orientation for range-based widgets."""
        if not isinstance(orientation, Orientation):
            raise GuiError(f'orientation must be an Orientation, got: {orientation}')
        self._horizontal = orientation

    def _graphical_range(self) -> int:
        """Return axis-aligned drawable range in pixels."""
        if self._horizontal == Orientation.Horizontal:
            return self._graphic_rect.width
        return self._graphic_rect.height

    def pixel_to_total(self, pixel_point: float, total_range: float) -> float:
        """Convert an axis pixel offset into logical range units."""
        graphical = self._graphical_range()
        if graphical <= 0:
            return 0.0
        return (float(pixel_point) * float(total_range)) / float(graphical)

    def total_to_pixel(self, total_point: float, total_range: float) -> int:
        """Convert a logical range value into an axis pixel offset."""
        if total_range <= 0:
            return 0
        return int((float(total_point) * float(self._graphical_range())) / float(total_range))

    def clamp_axis_position(self, value: float, total_range: float, snap_to_integer: bool = False) -> float:
        """Clamp an axis position into [0, total_range], with optional integer snapping."""
        safe_total = max(0.0, float(total_range))
        clamped = float(value)
        if clamped < 0.0:
            clamped = 0.0
        if clamped > safe_total:
            clamped = safe_total
        if snap_to_integer:
            return float(round(clamped))
        return clamped
