from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

from ..events import BaseEvent, GuiError

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class LifecycleCoordinator:
    """Owns screen/task-panel lifecycle callbacks and frame pre/post orchestration."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create LifecycleCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def run_postamble(self) -> None:
        """Run postamble."""
        for window in self.gui.windows:
            if window.visible:
                window.run_postamble()
        if self.gui.task_panel is not None and self.gui.task_panel.visible:
            self.gui.task_panel.run_postamble()
        self.gui.screen_lifecycle.run_postamble()

    def run_preamble(self) -> None:
        """Run preamble."""
        self.gui.screen_lifecycle.run_preamble()
        for window in self.gui.windows:
            if window.visible:
                window.run_preamble()
        if self.gui.task_panel is not None and self.gui.task_panel.visible:
            self.gui.task_panel.run_preamble()

    def set_screen_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[["BaseEvent"], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        """Set screen lifecycle."""
        if preamble is not None and not callable(preamble):
            raise GuiError('screen preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('screen event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('screen postamble must be callable or None')
        self.gui.screen_lifecycle.set_lifecycle(preamble, event_handler, postamble)

    def set_task_panel_lifecycle(
        self,
        preamble: Optional[Callable[[], None]] = None,
        event_handler: Optional[Callable[["BaseEvent"], None]] = None,
        postamble: Optional[Callable[[], None]] = None,
    ) -> None:
        """Set task panel lifecycle."""
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        if preamble is not None and not callable(preamble):
            raise GuiError('task panel preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('task panel event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('task panel postamble must be callable or None')
        self.gui.task_panel.set_lifecycle(preamble, event_handler, postamble)
