import os
from .utility.guimanager import GuiManager
from .utility.engine import Engine
from .utility.statemanager import StateManager
from .utility.constants import colours, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle


if os.name == 'nt':
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        # Keep compatibility with runtimes that do not expose SetProcessDPIAware such as WINE.
        pass
