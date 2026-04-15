from typing import Dict, Any, Tuple, Optional, Callable
from .guimanager import GuiManager

class StateManager:
    """Manages multiple GUI contexts for application state transitions.

    Allows switching between different GUI states (screens), each with its own
    GuiManager, event handlers, and lifecycle callbacks. Preserves mouse position
    when switching between contexts.
    """
    def __init__(self) -> None:
        self.contexts: Dict[str, Tuple[GuiManager, Any, Any, Callable[[], None], Callable[[Any], None], Callable[[], None]]] = {}
        self.active_context_name: Optional[str] = None
        self.is_running: bool = True

    def register_context(self, name: str, gui: GuiManager,
                         preamble: Callable[[], None], event_handler: Callable[[Any], None], postamble: Callable[[], None]) -> None:
        """Register a new application context.

        Args:
            name: Unique identifier for this context.
            gui: GuiManager instance for this context.
            preamble: Callback invoked before event processing each frame.
            event_handler: Callback to handle events for this context.
            postamble: Callback invoked after event processing each frame.
        """
        self.contexts[name] = (gui, gui.scheduler, gui.timers, preamble, event_handler, postamble)

    def switch_context(self, name: str) -> None:
        """Switch to a different application context.

        Preserves mouse position from the previous context. On the first context
        switch, mouse position defaults to (0, 0).

        Args:
            name: Name of the context to switch to.
        """
        if name in self.contexts:
            old_gui: Optional[GuiManager] = self.get_active_gui()
            # Preserve mouse position from old context if switching from an existing one
            if old_gui is not None:
                mouse_pos: Tuple[int, int] = old_gui.get_mouse_pos()
            else:
                mouse_pos = (0, 0)
            self.active_context_name = name
            new_gui: Optional[GuiManager] = self.get_active_gui()
            if new_gui:
                new_gui.set_mouse_pos(mouse_pos, True)

    def get_active_context(self) -> Optional[Tuple[GuiManager, Any, Any, Callable[[], None], Callable[[Any], None], Callable[[], None]]]:
        """Get the currently active context tuple.

        Returns:
            Tuple of (gui, scheduler, timers, preamble, event_handler, postamble) or None.
        """
        if self.active_context_name in self.contexts:
            return self.contexts[self.active_context_name]
        return None

    def get_active_gui(self) -> Optional[GuiManager]:
        """Get the GuiManager for the currently active context.

        Returns:
            GuiManager instance or None if no context is active.
        """
        context: Optional[Tuple[GuiManager, Any, Any, Callable[[], None], Callable[[Any], None], Callable[[], None]]] = self.get_active_context()
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
