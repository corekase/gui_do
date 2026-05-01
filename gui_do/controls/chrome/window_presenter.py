from typing import Optional
from pygame import Rect
from .window_control import WindowControl

class WindowPresenter:
    """
    Presenter/controller for a WindowControl. Responsible for creating controls, laying them out, and binding events.
    All business logic, event handling, and layout should be implemented here, not in WindowControl itself.
    """
    def __init__(self, window: WindowControl):
        self.window = window
        self.controls = []  # List of child controls managed by this presenter
        self._initialized = False

    def on_create(self):
        """Called when the window is created. Override to add controls and set up layout."""
        pass

    def on_show(self):
        """Called when the window is shown."""
        pass

    def on_close(self):
        """Called when the window is closed."""
        pass

    def on_resize(self, new_rect: Rect):
        """Called when the window is resized. Override to update layout."""
        pass

    def add_control(self, control):
        self.window.add(control)
        self.controls.append(control)

    def remove_control(self, control):
        self.window.remove(control)
        self.controls.remove(control)

    def clear_controls(self):
        self.window.clear_children()
        self.controls.clear()

    def handle_event(self, event):
        """Override to handle window-level events."""
        pass

    def update(self, dt_seconds: float):
        """Override to update window state per frame."""
        pass
