# gui is a package
import os
# import GuiManager
from .utility.guimanager import GuiManager
# import Engine and StateManager
from .utility.engine import Engine
from .utility.statemanager import StateManager
# import constants into the package namespace
from .utility.constants import colours, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle


if os.name == 'nt':
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        # Not available on all Windows runtimes (for example Wine/minimal shells).
        pass
