from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from ..events import GuiError
from ...widgets.window import Window

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class WorkspaceCoordinator:
    """Owns workspace-level container orchestration and stacking rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind workspace orchestration to a GUI manager."""
        self.gui: "GuiManager" = gui_manager

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

    def set_task_panel_hidden_peek_pixels(self, hidden_peek_pixels: int) -> None:
        """Set number of panel pixels shown while hidden."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_hidden_peek_pixels(hidden_peek_pixels)

    def set_task_panel_animation_step_px(self, animation_step_px: int) -> None:
        """Set vertical animation step in pixels for task-panel motion."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_animation_step_px(animation_step_px)

    def set_task_panel_animation_interval_ms(self, animation_interval_ms: float) -> None:
        """Set task-panel animation timer interval in milliseconds."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_animation_interval_ms(animation_interval_ms)

    def read_task_panel_settings(self) -> Dict[str, object]:
        """Return current task-panel behavior and geometry settings."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        panel = self.gui.task_panel
        return {
            'enabled': panel.visible,
            'auto_hide': panel.auto_hide,
            'panel_height': panel.panel_height,
            'left': panel.left,
            'width': panel.width,
            'hidden_peek_pixels': panel.hidden_peek_pixels,
            'animation_step_px': panel.animation_step_px,
            'animation_interval_ms': panel.animation_interval_ms,
            'backdrop_image': panel.backdrop_image,
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
