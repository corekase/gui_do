"""Typed status payload model for the Mandelbrot demo feature."""

from __future__ import annotations


from gui_do.events.status_event_base import StatusEventBase

MANDEL_KIND_STATUS = "status"

class MandelStatusEvent(StatusEventBase):
    """Typed status payload used for Mandelbrot status bus publication."""
    DEFAULT_KIND = MANDEL_KIND_STATUS


__all__ = ["MANDEL_KIND_STATUS", "MandelStatusEvent"]
