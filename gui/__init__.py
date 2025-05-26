# gui is a package
import os
# import utility functions into this package's namespace
from .utility import load_font, set_font, set_last_font, render_text
from .utility import centre, set_grid_properties, gridded
from .utility import image_alpha, file_resource, copy_graphic_area, gprint
# import GuiManager and controls into this package's namespace
from .guimanager import GuiManager
from .frame import Frame
from .label import Label
from .button import Button
from .scrollbar import Scrollbar
from .pushbuttongroup import PushButtonGroup, PushButtonKind
from .window import Window
# fix font graphical scaling issues with Windows
if os.name == 'nt':
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
