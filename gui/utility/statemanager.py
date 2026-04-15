from typing import Dict, Any, Tuple, Optional, Callable
from ..guimanager import GuiManager

class StateManager:
    def __init__(self) -> None:
        self.contexts: Dict[str, Tuple] = {}
        self.active_context_name: Optional[str] = None
        self.is_running: bool = True

    def register_context(self, name: str, gui: GuiManager,
                         preamble: Callable, event_handler: Callable, postamble: Callable):
        self.contexts[name] = (gui, gui.scheduler, gui.timers, preamble, event_handler, postamble)

    def switch_context(self, name: str):
        if name in self.contexts:
            old_gui = self.get_active_gui()
            mouse_pos = old_gui.get_mouse_pos() if old_gui else (0, 0)
            self.active_context_name = name
            new_gui = self.get_active_gui()
            if new_gui:
                new_gui.set_mouse_pos(mouse_pos, True)

    def get_active_context(self):
        if self.active_context_name in self.contexts:
            return self.contexts[self.active_context_name]
        return None

    def get_active_gui(self):
        context = self.get_active_context()
        return context[0] if context else None

    def set_running(self, running: bool) -> None:
        """Set the running state of the application."""
        self.is_running = running

    def __enter__(self) -> 'StateManager':
        """Enter context manager: initialize application state."""
        self.is_running = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager: cleanup and shutdown."""
        self.is_running = False
