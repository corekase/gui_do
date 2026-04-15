from types import TracebackType
from typing import Callable, Dict, Optional, Tuple, Type, Union
from .guimanager import GuiEvent, GuiManager
from .scheduler import Scheduler, TaskEvent, Timers

ContextType = Tuple[GuiManager, Scheduler, Timers, Callable[[], None], Callable[[Union[GuiEvent, TaskEvent]], None], Callable[[], None]]

class StateManager:
    """Manages multiple GUI contexts for application state transitions.

    Allows switching between different GUI states (screens), each with its own
    GuiManager, event handlers, and lifecycle callbacks. Preserves mouse position
    when switching between contexts.
    """
    def __init__(self) -> None:
        self._contexts: Dict[str, ContextType] = {}
        self._active_context_name: Optional[str] = None
        self.is_running: bool = True

    def register_context(self, name: str, gui: GuiManager,
                         preamble: Callable[[], None], event_handler: Callable[[Union[GuiEvent, TaskEvent]], None], postamble: Callable[[], None],
                         replace: bool = False) -> None:
        """Register a new application context.

        Args:
            name: Unique identifier for this context.
            gui: GuiManager instance for this context.
            preamble: Callback invoked before event processing each frame.
            event_handler: Callback to handle events for this context.
            postamble: Callback invoked after event processing each frame.
            replace: If True, overwrite an existing context with the same name.
                     If False, raise KeyError when name already exists.
        """
        if not replace and name in self._contexts:
            raise KeyError(f'duplicate context: {name}')
        self._contexts[name] = (gui, gui.scheduler, gui.timers, preamble, event_handler, postamble)

    def switch_context(self, name: str) -> None:
        """Switch to a different application context.

        Preserves mouse position from the previous context. On the first context
        switch, mouse position defaults to (0, 0).

        Args:
            name: Name of the context to switch to.
        """
        if name not in self._contexts:
            raise KeyError(f'unknown context: {name}')

        old_gui: Optional[GuiManager] = self.get_active_gui()
        # Preserve mouse position from old context if switching from an existing one
        if old_gui is not None:
            mouse_pos: Tuple[int, int] = old_gui.get_mouse_pos()
        else:
            mouse_pos = (0, 0)
        self._active_context_name = name
        new_gui: Optional[GuiManager] = self.get_active_gui()
        if new_gui:
            new_gui.set_mouse_pos(mouse_pos, True)

    def get_active_context(self) -> Optional[ContextType]:
        """Get the currently active context tuple.

        Returns:
            Tuple of (gui, scheduler, timers, preamble, event_handler, postamble) or None.
        """
        if self._active_context_name in self._contexts:
            return self._contexts[self._active_context_name]
        return None

    def get_active_gui(self) -> Optional[GuiManager]:
        """Get the GuiManager for the currently active context.

        Returns:
            GuiManager instance or None if no context is active.
        """
        context: Optional[ContextType] = self.get_active_context()
        return context[0] if context else None

    def set_running(self, running: bool) -> None:
        """Set the running state of the application."""
        self.is_running = running

    def __enter__(self) -> 'StateManager':
        """Enter context manager: initialize application state."""
        self.is_running = True
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        """Exit context manager: cleanup and shutdown."""
        self.is_running = False
