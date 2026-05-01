from typing import Optional
from pygame import Rect
from .window_control import WindowControl


class WindowPresenter:
    """
    Presenter/controller for a WindowControl.

    The presenter owns window content controls and window-level behavior while
    WindowControl owns chrome and host-level routing concerns.
    """

    def __init__(self, window: Optional[WindowControl] = None):
        self.window = window
        self.controls = []

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def on_attach(self, window: WindowControl) -> None:
        """Called when this presenter is attached to a window."""

    def on_detach(self, window: WindowControl) -> None:
        """Called when this presenter is detached from a window."""

    def on_create(self):
        """Called once when presenter wiring is complete. Override to build controls."""
        return None

    def on_show(self):
        """Called when the window becomes visible."""

    def on_close(self):
        """Called when the window closes or is hidden."""

    def on_hide(self):
        """Called when the window becomes hidden."""

    def on_resize(self, new_rect: Rect):
        """Called when the window's outer rect size changes."""

    def before_update(self, dt_seconds: float):
        """Called before window child updates run for this frame."""

    def after_update(self, dt_seconds: float):
        """Called after window child updates run for this frame."""

    def add_control(self, control):
        if self.window is None:
            raise RuntimeError("WindowPresenter.add_control called before attach")
        self.window.add(control)
        self.controls.append(control)
        return control

    def remove_control(self, control):
        if self.window is None:
            return False
        removed = self.window.remove(control)
        if removed and control in self.controls:
            self.controls.remove(control)
        return removed

    def clear_controls(self, *, dispose: bool = False):
        if self.window is None:
            self.controls.clear()
            return 0
        removed = self.window.clear_children(dispose=dispose)
        self.controls.clear()
        return removed

    def handle_event(self, event):
        """Override to handle window-level events before child dispatch."""
        return False

    def update(self, dt_seconds: float):
        """Override to update presenter-level state per frame."""
