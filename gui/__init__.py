# gui is a package
import os
# import GuiManager
from .guimanager import GuiManager
# import Engine and StateManager
from .engine import Engine
from .statemanager import StateManager
# import constants into the package namespace
from .utility.values.constants import colours, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle
# fix font graphical scaling issues with Windows
if os.name == 'nt':
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
