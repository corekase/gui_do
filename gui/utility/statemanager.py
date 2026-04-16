import logging
from types import TracebackType
from typing import Dict, Optional, Tuple, Type
from .guimanager import GuiManager

_logger = logging.getLogger(__name__)

class StateManager:
    """Manages multiple GUI contexts for application state transitions.

    Allows switching between different GUI states (screens), each with its own
    GuiManager. Preserves mouse position when switching between contexts.
    """
    def __init__(self) -> None:
        self._contexts: Dict[str, GuiManager] = {}
        self._active_context_name: Optional[str] = None
        self.is_running: bool = True

    def register_context(self, name: str, gui: GuiManager, replace: bool = False) -> None:
        """Register a new application context.

        Args:
            name: Unique identifier for this context.
            gui: GuiManager instance for this context.
            replace: If True, overwrite an existing context with the same name.
                     If False, raise KeyError when name already exists.
        """
        if not isinstance(name, str) or name == '':
            raise ValueError('context name must be a non-empty string')
        if not isinstance(gui, GuiManager):
            raise TypeError('gui must be a GuiManager instance')
        if not replace and name in self._contexts:
            raise KeyError(f'duplicate context: {name}')
        self._contexts[name] = gui

    def switch_context(self, name: str) -> None:
        """Switch to a different application context.

        Preserves mouse position from the previous context. On the first context
        switch, mouse position defaults to (0, 0).

        Args:
            name: Name of the context to switch to.
        """
        if not isinstance(name, str) or name == '':
            raise ValueError('context name must be a non-empty string')
        if name not in self._contexts:
            raise KeyError(f'unknown context: {name}')
        if self._active_context_name == name:
            return

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

    def get_active_gui(self) -> Optional[GuiManager]:
        """Get the GuiManager for the currently active context.

        Returns:
            GuiManager instance or None if no context is active.
        """
        if self._active_context_name in self._contexts:
            return self._contexts[self._active_context_name]
        return None

    def set_running(self, running: bool) -> None:
        """Set the running state of the application."""
        if not isinstance(running, bool):
            raise TypeError('running must be a bool')
        self.is_running = running

    def __enter__(self) -> 'StateManager':
        """Enter context manager: initialize application state."""
        self.is_running = True
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        """Exit context manager: cleanup and shutdown."""
        for name, gui in self._contexts.items():
            scheduler = gui.scheduler
            try:
                scheduler.shutdown()
            except Exception as exc:
                # Shutdown is best-effort; report failures without masking prior exceptions.
                _logger.warning(
                    'Failed to shutdown scheduler for context "%s": %s: %s',
                    name,
                    type(exc).__name__,
                    exc,
                )
        self.is_running = False
