from __future__ import annotations

from dataclasses import dataclass
from pygame import Rect

from ..events import GuiError, Orientation


@dataclass(frozen=True)
class RangeAxisDomain:
    """Axis-specific pixel/logical conversion domain."""

    total_range: float
    graphical_range: int

    def pixel_to_total(self, pixel_point: float) -> float:
        """Convert a pixel offset to logical range units."""
        if self.graphical_range <= 0:
            return 0.0
        return (float(pixel_point) * self.total_range) / float(self.graphical_range)

    def total_to_pixel(self, total_point: float) -> int:
        """Convert a logical value to a pixel offset."""
        if self.total_range <= 0.0:
            return 0
        return int((float(total_point) * float(self.graphical_range)) / self.total_range)

    def clamp(self, value: float, snap_to_integer: bool = False) -> float:
        """Clamp to [0, total_range], optionally snapping to an integer."""
        clamped = float(value)
        if clamped < 0.0:
            clamped = 0.0
        if clamped > self.total_range:
            clamped = self.total_range
        if snap_to_integer:
            return float(round(clamped))
        return clamped


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

    def _range_domain(self, total_range: float) -> RangeAxisDomain:
        """Build the conversion domain for the current axis."""
        safe_total = max(0.0, float(total_range))
        return RangeAxisDomain(total_range=safe_total, graphical_range=self._graphical_range())

    def pixel_to_total(self, pixel_point: float, total_range: float) -> float:
        """Convert an axis pixel offset into logical range units."""
        return self._range_domain(total_range).pixel_to_total(pixel_point)

    def total_to_pixel(self, total_point: float, total_range: float) -> int:
        """Convert a logical range value into an axis pixel offset."""
        return self._range_domain(total_range).total_to_pixel(total_point)

    def clamp_axis_position(self, value: float, total_range: float, snap_to_integer: bool = False) -> float:
        """Clamp an axis position into [0, total_range], with optional integer snapping."""
        return self._range_domain(total_range).clamp(value, snap_to_integer)
