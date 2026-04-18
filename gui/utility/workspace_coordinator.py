from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from .events import GuiError
from ..widgets.window import Window as Window

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class WorkspaceCoordinator:
    """Owns workspace-level container orchestration and stacking rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind workspace orchestration to a GUI manager."""
        self.gui: "GuiManager" = gui_manager

    def begin_task_panel(self) -> None:
        """Route subsequent widget creation into the task panel container."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.workspace_state.task_panel_capture = True
        self.gui.workspace_state.active_object = None

    def end_task_panel(self) -> None:
        """Stop routing new widgets into task panel capture mode."""
        self.gui.workspace_state.task_panel_capture = False

    def set_task_panel_enabled(self, enabled: bool) -> None:
        """Set task-panel visibility and disable capture when hidden."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_visible(enabled)
        if not enabled:
            self.gui.workspace_state.task_panel_capture = False

    def set_task_panel_auto_hide(self, auto_hide: bool) -> None:
        """Set task-panel auto-hide behavior."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_auto_hide(auto_hide)

    def set_task_panel_reveal_pixels(self, reveal_pixels: int) -> None:
        """Set number of reveal pixels shown while panel is hidden."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_reveal_pixels(reveal_pixels)

    def set_task_panel_movement_step(self, movement_step: int) -> None:
        """Set vertical animation step for task-panel reveal/hide."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_movement_step(movement_step)

    def set_task_panel_timer_interval(self, timer_interval: float) -> None:
        """Set task-panel animation timer interval."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_timer_interval(timer_interval)

    def read_task_panel_settings(self) -> Dict[str, object]:
        """Return current task-panel behavior and geometry settings."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        panel = self.gui.task_panel
        return {
            'enabled': panel.visible,
            'auto_hide': panel.auto_hide,
            'reveal_pixels': panel.reveal_pixels,
            'movement_step': panel.movement_step,
            'timer_interval': panel.timer_interval,
            'rect': panel.get_rect(),
        }

    def lower_window(self, window: Window) -> None:
        """Move a registered window to the bottom of z-order."""
        resolved_window = self.gui.object_registry.resolve_registered_window(window)
        if resolved_window is None:
            return
        self.gui.windows.remove(resolved_window)
        self.gui.windows.insert(0, resolved_window)

    def raise_window(self, window: Window) -> None:
        """Move a registered window to the top of z-order."""
        resolved_window = self.gui.object_registry.resolve_registered_window(window)
        if resolved_window is None:
            return
        self.gui.windows.remove(resolved_window)
        self.gui.windows.append(resolved_window)
