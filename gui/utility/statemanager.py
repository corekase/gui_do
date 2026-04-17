import logging
from types import TracebackType
from typing import Dict, Optional, Tuple, Type
from .guimanager import GuiManager

_logger = logging.getLogger(__name__)

class StateManager:
    """Registers named GUI contexts and tracks the active one."""

    def __init__(self) -> None:
        self._contexts: Dict[str, GuiManager] = {}
        self._active_context_name: Optional[str] = None
        self.is_running: bool = True

    def get_active_gui(self) -> Optional[GuiManager]:
        """Return the active GuiManager, or None when unset."""
        if self._active_context_name in self._contexts:
            return self._contexts[self._active_context_name]
        return None

    def register_context(self, name: str, gui: GuiManager, replace: bool = False) -> None:
        """Register or replace a named GuiManager context."""
        if not isinstance(name, str) or name == '':
            raise ValueError('context name must be a non-empty string')
        if not isinstance(gui, GuiManager):
            raise TypeError('gui must be a GuiManager instance')
        if not replace and name in self._contexts:
            raise KeyError(f'duplicate context: {name}')
        self._contexts[name] = gui

    def set_running(self, running: bool) -> None:
        """Set loop running state."""
        if not isinstance(running, bool):
            raise TypeError('running must be a bool')
        self.is_running = running

    def switch_context(self, name: str) -> None:
        """Activate context by name and carry over current mouse position."""
        if not isinstance(name, str) or name == '':
            raise ValueError('context name must be a non-empty string')
        if name not in self._contexts:
            raise KeyError(f'unknown context: {name}')
        if self._active_context_name == name:
            return
        old_gui: Optional[GuiManager] = self.get_active_gui()
        if old_gui is not None:
            mouse_pos: Tuple[int, int] = old_gui.get_mouse_pos()
        else:
            mouse_pos = (0, 0)
        self._active_context_name = name
        new_gui: Optional[GuiManager] = self.get_active_gui()
        if new_gui:
            new_gui.set_mouse_pos(mouse_pos, True)

    def __enter__(self) -> 'StateManager':
        """Enter running state for engine loop usage."""
        self.is_running = True
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]) -> None:
        """Shutdown registered schedulers and leave running state."""
        for name, gui in self._contexts.items():
            scheduler = gui.scheduler
            try:
                scheduler.shutdown()
            except Exception as exc:
                _logger.warning(
                    'Failed to shutdown scheduler for context "%s": %s: %s',
                    name,
                    type(exc).__name__,
                    exc,
                )
        self.is_running = False
