import os

"""Public package entry point for core GUI runtime classes and enums."""

from .utility.gui_manager import GuiManager
from .utility.engine import Engine
from .utility.state_manager import StateManager
from .utility.events import colours, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle
from .utility.gui_utils.task_panel_settings import TaskPanelSettings
from .utility.gui_utils.mouse_input_state import MouseInputState


def _enable_windows_dpi_awareness() -> None:
    """Enable process DPI awareness on Windows to improve pixel alignment."""
    # Keep non-Windows import side effects minimal.
    if os.name != 'nt':
        return
    # Import lazily so non-Windows environments avoid ctypes dependency paths.
    import ctypes
    # Raise backend errors to preserve strict package-init behavior contracts.
    ctypes.windll.user32.SetProcessDPIAware()


_enable_windows_dpi_awareness()
