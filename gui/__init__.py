import os
from .utility.gui_manager import GuiManager
from .utility.engine import Engine
from .utility.state_manager import StateManager
from .utility.events import colours, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle


def _enable_windows_dpi_awareness() -> None:
    if os.name != 'nt':
        return
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()


_enable_windows_dpi_awareness()
