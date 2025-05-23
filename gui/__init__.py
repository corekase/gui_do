import os
# import utility module into this packages namespace
from . import utility
from .utility import cut, cut_tile, image_alpha, file_resource, padding, render_text, centre
from .utility import load_font, set_font
# import gui manager and controls into this packages namespace
from .guimanager import GuiManager
from .widget import Widget
from .frame import Frame
from .label import Label
from .button import Button
from .scrollbar import Scrollbar
from .pushbuttongroup import PushButtonGroup

if os.name == 'nt':
    # fixes graphical scaling issues with Windows
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
