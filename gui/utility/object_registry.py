from typing import Any, Optional, TYPE_CHECKING, TypeVar, cast

from .constants import GuiError
from .widget import Widget
from ..widgets.window import Window as gWindow

if TYPE_CHECKING:
    from .guimanager import GuiManager

TGuiObject = TypeVar("TGuiObject", gWindow, Widget)


class GuiObjectRegistry:
    """Owns GUI object registration and container assignment rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def register(self, gui_object: TGuiObject) -> TGuiObject:
        if gui_object is None:
            raise GuiError('gui_object cannot be None')
        if not isinstance(gui_object, (gWindow, Widget)):
            raise GuiError('gui_object must be a Window or Widget instance')
        if self.is_registered_object(gui_object):
            raise GuiError(f'gui_object is already registered: {self.describe_gui_object(gui_object)}')
        if isinstance(gui_object, gWindow):
            if self.gui._task_panel_capture and self.gui.task_panel is not None:
                raise GuiError('window nesting inside task panel is not supported; call end_task_panel() before creating a window')
            self.gui.windows.append(gui_object)
            self.gui._active_object = gui_object
            return gui_object

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
        added_to_task_panel = False
        if self.gui._task_panel_capture and self.gui.task_panel is not None:
            gui_object.window = cast(Any, self.gui.task_panel)
            gui_object.surface = self.gui.task_panel.surface
            self.gui.task_panel.widgets.append(gui_object)
            added_to_task_panel = True
        elif active_window is not None:
            gui_object.window = active_window
            gui_object.surface = active_window.surface
            active_window.widgets.append(gui_object)
        else:
            gui_object.window = None
            gui_object.surface = self.gui.surface
            self.gui.widgets.append(gui_object)

        post_add = getattr(gui_object, '_on_added_to_gui', None)
        if callable(post_add):
            try:
                post_add()
            except Exception:
                if added_to_task_panel and self.gui.task_panel is not None and gui_object in self.gui.task_panel.widgets:
                    self.gui.task_panel.widgets.remove(gui_object)
                elif active_window is not None:
                    if gui_object in active_window.widgets:
                        active_window.widgets.remove(gui_object)
                else:
                    if gui_object in self.gui.widgets:
                        self.gui.widgets.remove(gui_object)
                gui_object.window = None
                gui_object.surface = None
                raise
        return gui_object

    def describe_gui_object(self, gui_object: TGuiObject) -> str:
        if isinstance(gui_object, Widget):
            return f'{type(gui_object).__name__} id={getattr(gui_object, "id", "<missing>")}'
        if isinstance(gui_object, gWindow):
            return (
                f'{type(gui_object).__name__} '
                f'pos=({gui_object.x},{gui_object.y}) size=({gui_object.width},{gui_object.height})'
            )
        return type(gui_object).__name__

    def describe_incoming_widget_container(self) -> str:
        if self.gui._task_panel_capture and self.gui.task_panel is not None:
            return 'task_panel'
        window = self.resolve_active_object()
        if window is None:
            return 'screen'
        return f'window pos=({window.x},{window.y}) size=({window.width},{window.height})'

    def describe_widget_container(self, widget: Widget) -> str:
        if self.gui.task_panel is not None and widget in self.gui.task_panel.widgets:
            return 'task_panel'
        window = getattr(widget, 'window', None)
        if window is None or not isinstance(window, gWindow):
            return 'screen'
        return f'window pos=({window.x},{window.y}) size=({window.width},{window.height})'

    def find_widget_id_conflict(self, widget_id: str, candidate: Widget) -> Optional[Widget]:
        for widget in self.gui.widgets:
            if widget is not candidate and widget.id == widget_id:
                return widget
        if self.gui.task_panel is not None:
            for widget in self.gui.task_panel.widgets:
                if widget is not candidate and widget.id == widget_id:
                    return widget
        for window in self.gui.windows:
            for widget in window.widgets:
                if widget is not candidate and widget.id == widget_id:
                    return widget
        return None

    def is_registered_button_group(self, button) -> bool:
        if button.surface is None:
            return True
        return self.is_registered_object(button)

    def is_registered_object(self, gui_object: TGuiObject) -> bool:
        if isinstance(gui_object, gWindow):
            return gui_object in self.gui.windows
        if isinstance(gui_object, Widget):
            if gui_object in self.gui.widgets:
                return True
            if self.gui.task_panel is not None and gui_object in self.gui.task_panel.widgets:
                return True
            for window in self.gui.windows:
                if gui_object in window.widgets:
                    return True
        return False

    def resolve_active_object(self) -> Optional[gWindow]:
        if self.gui._active_object is None:
            return None
        if self.gui._active_object not in self.gui.windows:
            self.gui._active_object = None
            return None
        return self.gui._active_object
