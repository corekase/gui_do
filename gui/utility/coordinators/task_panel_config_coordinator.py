from __future__ import annotations

from typing import Any, List, TYPE_CHECKING, cast

from ..events import GuiError
from ..gui_utils.task_panel_settings import TaskPanelSettings
from ..intermediates.widget import Widget

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class TaskPanelConfigCoordinator:
    """Owns task-panel configuration validation and atomic panel replacement."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create TaskPanelConfigCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def set_task_panel_settings(self, settings: TaskPanelSettings) -> None:
        """Apply task panel settings."""
        from ..gui_utils.task_panel import _ManagedTaskPanel

        if not isinstance(settings, TaskPanelSettings):
            raise GuiError('task panel settings must be a TaskPanelSettings instance')

        panel_height = settings.panel_height
        left = settings.left
        width = settings.width
        hidden_peek_pixels = settings.hidden_peek_pixels
        auto_hide = settings.auto_hide
        animation_interval_ms = settings.animation_interval_ms
        animation_step_px = settings.animation_step_px
        backdrop_image = settings.backdrop_image
        preamble = settings.preamble
        event_handler = settings.event_handler
        postamble = settings.postamble

        if type(panel_height) is not int or panel_height <= 0:
            raise GuiError(f'task_panel_panel_height must be a positive int, got: {panel_height}')
        if type(left) is not int:
            raise GuiError(f'task_panel_left must be an int, got: {left}')
        if width is not None and type(width) is not int:
            raise GuiError(f'task_panel_width must be an int or None, got: {width}')
        if type(hidden_peek_pixels) is not int or hidden_peek_pixels < 1:
            raise GuiError(f'task_panel_hidden_peek_pixels must be >= 1, got: {hidden_peek_pixels}')
        if type(auto_hide) is not bool:
            raise GuiError('task_panel_auto_hide must be a bool')
        if type(animation_step_px) is not int or animation_step_px <= 0:
            raise GuiError(f'task_panel_animation_step_px must be > 0, got: {animation_step_px}')
        if isinstance(animation_interval_ms, bool) or not isinstance(animation_interval_ms, (int, float)) or animation_interval_ms <= 0:
            raise GuiError(f'task_panel_animation_interval_ms must be > 0, got: {animation_interval_ms}')
        if backdrop_image is not None and (not isinstance(backdrop_image, str) or backdrop_image == ''):
            raise GuiError(f'task_panel_backdrop_image must be a non-empty string or None, got: {backdrop_image!r}')
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
            panel_height,
            left,
            width,
            hidden_peek_pixels,
            auto_hide,
            animation_interval_ms,
            animation_step_px,
            backdrop_image,
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
