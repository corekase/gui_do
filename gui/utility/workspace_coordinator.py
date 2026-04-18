from typing import Dict, TYPE_CHECKING

from .constants import GuiError
from ..widgets.window import Window as gWindow

if TYPE_CHECKING:
    from .guimanager import GuiManager


class WorkspaceCoordinator:
    """Owns workspace-level container orchestration and stacking rules."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def begin_task_panel(self) -> None:
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.workspace_state.task_panel_capture = True
        self.gui.workspace_state.active_object = None

    def end_task_panel(self) -> None:
        self.gui.workspace_state.task_panel_capture = False

    def set_task_panel_enabled(self, enabled: bool) -> None:
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_visible(enabled)
        if not enabled:
            self.gui.workspace_state.task_panel_capture = False

    def set_task_panel_auto_hide(self, auto_hide: bool) -> None:
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_auto_hide(auto_hide)

    def set_task_panel_reveal_pixels(self, reveal_pixels: int) -> None:
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_reveal_pixels(reveal_pixels)

    def set_task_panel_movement_step(self, movement_step: int) -> None:
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_movement_step(movement_step)

    def set_task_panel_timer_interval(self, timer_interval: float) -> None:
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        self.gui.task_panel.set_timer_interval(timer_interval)

    def read_task_panel_settings(self) -> Dict[str, object]:
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

    def lower_window(self, window: gWindow) -> None:
        self.gui._resolve_active_object()
        if window not in self.gui.windows:
            if self.gui.workspace_state.active_object is window:
                self.gui.workspace_state.active_object = None
            return
        self.gui.windows.remove(window)
        self.gui.windows.insert(0, window)

    def raise_window(self, window: gWindow) -> None:
        self.gui._resolve_active_object()
        if window not in self.gui.windows:
            if self.gui.workspace_state.active_object is window:
                self.gui.workspace_state.active_object = None
            return
        self.gui.windows.remove(window)
        self.gui.windows.append(window)
