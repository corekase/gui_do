from typing import Any, Callable, List, Optional, TYPE_CHECKING, cast

from .constants import BaseEvent, GuiError
from .widget import Widget

if TYPE_CHECKING:
    from .guimanager import GuiManager


class TaskPanelConfigCoordinator:
    """Owns task-panel configuration validation and atomic panel replacement."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def configure_task_panel(
        self,
        *,
        height: int = 38,
        x: int = 0,
        reveal_pixels: int = 4,
        auto_hide: bool = True,
        timer_interval: float = 16.0,
        movement_step: int = 4,
        backdrop: Optional[str] = None,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[[BaseEvent], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        from .task_panel import _ManagedTaskPanel

        if type(height) is not int or height <= 0:
            raise GuiError(f'task_panel_height must be a positive int, got: {height}')
        if type(x) is not int:
            raise GuiError(f'task_panel_x must be an int, got: {x}')
        if type(reveal_pixels) is not int or reveal_pixels < 1:
            raise GuiError(f'task_panel_reveal_pixels must be >= 1, got: {reveal_pixels}')
        if type(auto_hide) is not bool:
            raise GuiError('task_panel_auto_hide must be a bool')
        if type(movement_step) is not int or movement_step <= 0:
            raise GuiError(f'task_panel_movement_step must be > 0, got: {movement_step}')
        if isinstance(timer_interval, bool) or not isinstance(timer_interval, (int, float)) or timer_interval <= 0:
            raise GuiError(f'task_panel_timer_interval must be > 0, got: {timer_interval}')
        if backdrop is not None and (not isinstance(backdrop, str) or backdrop == ''):
            raise GuiError(f'task_panel_backdrop must be a non-empty string or None, got: {backdrop!r}')
        if preamble is not None and not callable(preamble):
            raise GuiError('task panel preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('task panel event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('task panel postamble must be callable or None')

        old_panel = self.gui.task_panel
        existing_widgets: List[Widget] = []
        existing_visible = True
        if old_panel is not None:
            existing_widgets = list(old_panel.widgets)
            existing_visible = old_panel.visible

        panel = _ManagedTaskPanel(
            self.gui,
            height,
            x,
            reveal_pixels,
            auto_hide,
            timer_interval,
            movement_step,
            backdrop,
            preamble,
            event_handler,
            postamble,
        )

        if old_panel is not None:
            old_panel.dispose()

        if existing_widgets:
            panel.widgets = existing_widgets
            for widget in panel.widgets:
                widget.window = cast(Any, panel)
                widget.surface = panel.surface

        if old_panel is not None:
            panel.set_visible(existing_visible)
            if not existing_visible:
                self.gui.workspace_state.task_panel_capture = False

        self.gui.task_panel = panel
