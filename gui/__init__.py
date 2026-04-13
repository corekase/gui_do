# gui is a package
import os
# import GuiManager and widgets into this package's namespace
from .guimanager import GuiManager
from .values.decorations import _init_decorations
_init_decorations()
# import constants into the package namespace
from .values.constants import colours, GKind, GType, HorV, SArrows, BStyle
from .widgets.canvas import CKind
# import scheduler
from .scheduler import Scheduler, TKind
# fix font graphical scaling issues with Windows
if os.name == 'nt':
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
