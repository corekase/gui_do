from typing import Callable, Optional, TYPE_CHECKING

from .constants import BaseEvent, GuiError

if TYPE_CHECKING:
    from .guimanager import GuiManager


def _noop() -> None:
    pass


def _noop_event(_: BaseEvent) -> None:
    pass


class ScreenLifecycle:
    """Owns screen-level lifecycle callbacks and event handler."""

    def __init__(self) -> None:
        self.preamble: Callable[[], None] = _noop
        self.event_handler: Callable[[BaseEvent], None] = _noop_event
        self.postamble: Callable[[], None] = _noop

    def set_lifecycle(
        self,
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        self.preamble = preamble if preamble is not None else _noop
        self.event_handler = event_handler if event_handler is not None else _noop_event
        self.postamble = postamble if postamble is not None else _noop

    def run_preamble(self) -> None:
        self.preamble()

    def run_postamble(self) -> None:
        self.postamble()

    def handle_event(self, event: BaseEvent) -> None:
        self.event_handler(event)


class LifecycleCoordinator:
    """Owns screen/task-panel lifecycle callbacks and frame pre/post orchestration."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def run_postamble(self) -> None:
        for window in self.gui.windows:
            if window.visible:
                window.run_postamble()
        if self.gui.task_panel is not None and self.gui.task_panel.visible:
            self.gui.task_panel.run_postamble()
        self.gui.screen_lifecycle.run_postamble()

    def run_preamble(self) -> None:
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
        if self.gui.task_panel is None:
            raise GuiError('task panel is disabled for this gui manager')
        if preamble is not None and not callable(preamble):
            raise GuiError('task panel preamble must be callable or None')
        if event_handler is not None and not callable(event_handler):
            raise GuiError('task panel event_handler must be callable or None')
        if postamble is not None and not callable(postamble):
            raise GuiError('task panel postamble must be callable or None')
        self.gui.task_panel.set_lifecycle(preamble, event_handler, postamble)
