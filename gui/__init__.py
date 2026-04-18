import os
from .utility.gui_manager import GuiManager
from .utility.engine import Engine
from .utility.state_manager import StateManager
from .utility.events import colours, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle


if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
