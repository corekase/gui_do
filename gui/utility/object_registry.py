from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING, TypeVar, cast

from .events import GuiError
from .intermediates.widget import Widget
from ..widgets.window import Window

if TYPE_CHECKING:
    from .gui_manager import GuiManager

TGuiObject = TypeVar("TGuiObject", Window, Widget)


class GuiObjectRegistry:
    """Owns GUI object registration and container assignment rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind registry behavior to a specific `GuiManager` instance."""
        self.gui: "GuiManager" = gui_manager

    def _iter_registered_widgets(self):
        """Yield all registered widgets across screen, task panel, and windows."""
        for widget in self.gui.widgets:
            yield widget
        if self.gui.task_panel is not None:
            for widget in self.gui.task_panel.widgets:
                yield widget
        for window in self.gui.windows:
            for widget in window.widgets:
                yield widget

    def _detach_widget_from_current_container(self, gui_object: Widget, active_window: Optional[Window], added_to_task_panel: bool) -> None:
        """Detach a widget from whichever container received it during registration."""
        if added_to_task_panel and self.gui.task_panel is not None and gui_object in self.gui.task_panel.widgets:
            self.gui.task_panel.widgets.remove(gui_object)
            return
        if active_window is not None and gui_object in active_window.widgets:
            active_window.widgets.remove(gui_object)
            return
        if gui_object in self.gui.widgets:
            self.gui.widgets.remove(gui_object)

    def _reset_widget_registration(self, gui_object: Widget, active_window: Optional[Window], added_to_task_panel: bool) -> None:
        """Rollback a failed widget registration attempt to a clean state."""
        self._detach_widget_from_current_container(gui_object, active_window, added_to_task_panel)
        gui_object.window = None
        gui_object.surface = None

    def _resolve_widget_attach_target(self, active_window: Optional[Window]):
        """Resolve container, target surface, and widget list for new widget attach."""
        if self.gui.workspace_state.task_panel_capture and self.gui.task_panel is not None:
            return cast(Any, self.gui.task_panel), self.gui.task_panel.surface, self.gui.task_panel.widgets, True
        if active_window is not None:
            return active_window, active_window.surface, active_window.widgets, False
        return None, self.gui.surface, self.gui.widgets, False

    def _attach_widget_to_container(self, gui_object: Widget, active_window: Optional[Window]) -> bool:
        """Attach a widget to its resolved container and initialize host pointers."""
        window, surface, widgets, added_to_task_panel = self._resolve_widget_attach_target(active_window)
        gui_object.window = window
        gui_object.surface = surface
        widgets.append(gui_object)
        return added_to_task_panel

    def register(self, gui_object: TGuiObject) -> TGuiObject:
        """Register a window or widget with validation and rollback safeguards."""
        if gui_object is None:
            raise GuiError('gui_object cannot be None')
        if not isinstance(gui_object, (Window, Widget)):
            raise GuiError('gui_object must be a Window or Widget instance')
        if self.is_registered_object(gui_object):
            raise GuiError(f'gui_object is already registered: {self.describe_gui_object(gui_object)}')
        if isinstance(gui_object, Window):
            if self.gui.workspace_state.task_panel_capture and self.gui.task_panel is not None:
                raise GuiError('window nesting inside task panel is not supported')
            self.gui.windows.append(gui_object)
            self.gui.workspace_state.active_object = gui_object
            on_registered = getattr(self.gui, '_on_window_registered', None)
            if callable(on_registered):
                on_registered(gui_object)
            return gui_object

        # Widgets require unique, non-empty ids within all registered containers.
        if not isinstance(gui_object.id, str) or gui_object.id == '':
            raise GuiError('widget id must be a non-empty string')
        conflict = self.find_widget_id_conflict(gui_object.id, gui_object)
        if conflict is not None:
            raise GuiError(
                f'duplicate widget id: {gui_object.id}; '
                f'incoming={self.describe_gui_object(gui_object)} '
                f'on {self.describe_incoming_widget_container()}; '
                f'conflict={self.describe_gui_object(conflict)} '
                f'on {self.describe_widget_container(conflict)}'
            )
        active_window = self.resolve_active_object()
        added_to_task_panel = self._attach_widget_to_container(gui_object, active_window)

        # Invoke optional post-add hooks, rolling back registration if they fail.
        post_add = getattr(gui_object, '_on_added_to_gui', None)
        if callable(post_add):
            try:
                post_add()
            except Exception:
                self._reset_widget_registration(gui_object, active_window, added_to_task_panel)
                raise
        return gui_object

    def describe_gui_object(self, gui_object: TGuiObject) -> str:
        """Return a short descriptive string for diagnostics and error reporting."""
        if isinstance(gui_object, Widget):
            return f'{type(gui_object).__name__} id={getattr(gui_object, "id", "<missing>")}'
        if isinstance(gui_object, Window):
            return (
                f'{type(gui_object).__name__} '
                f'pos=({gui_object.x},{gui_object.y}) size=({gui_object.width},{gui_object.height})'
            )
        return type(gui_object).__name__

    def describe_incoming_widget_container(self) -> str:
        """Describe where a newly registered widget would be attached."""
        if self.gui.workspace_state.task_panel_capture and self.gui.task_panel is not None:
            return 'task_panel'
        window = self.resolve_active_object()
        if window is None:
            return 'screen'
        return f'window pos=({window.x},{window.y}) size=({window.width},{window.height})'

    def describe_widget_container(self, widget: Widget) -> str:
        """Describe the current container that owns the given widget."""
        if self.gui.task_panel is not None and widget in self.gui.task_panel.widgets:
            return 'task_panel'
        window = getattr(widget, 'window', None)
        if window is None or not isinstance(window, Window):
            return 'screen'
        return f'window pos=({window.x},{window.y}) size=({window.width},{window.height})'

    def find_widget_id_conflict(self, widget_id: str, candidate: Widget) -> Optional[Widget]:
        """Return first widget using `widget_id`, excluding the candidate widget."""
        for widget in self._iter_registered_widgets():
            if widget is not candidate and widget.id == widget_id:
                return widget
        return None

    def is_registered_button_group(self, button) -> bool:
        """Return button-group registration status."""
        return self.is_registered_object(button)

    def is_registered_object(self, gui_object: TGuiObject) -> bool:
        """Return whether a window/widget is currently registered in this GUI."""
        if isinstance(gui_object, Window):
            return gui_object in self.gui.windows
        if isinstance(gui_object, Widget):
            for widget in self._iter_registered_widgets():
                if gui_object is widget:
                    return True
        return False

    def resolve_active_object(self) -> Optional[Window]:
        """Resolve and return the current active window if still valid."""
        return self.gui.workspace_state.resolve_active_object(self.gui.windows)

    def resolve_registered_window(self, window: Optional[Window]) -> Optional[Window]:
        """Return a valid registered window or clear stale active-window references."""
        self.resolve_active_object()
        if window is None:
            return None
        if window not in self.gui.windows:
            if self.gui.workspace_state.active_object is window:
                self.gui.workspace_state.active_object = None
            return None
        return window
