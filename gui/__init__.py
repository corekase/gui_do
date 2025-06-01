# gui is a package
import os
# import utility functions into this package's namespace
from .utility import set_surface, load_font, set_font, set_last_font, render_text
from .utility import centre, set_grid_properties, gridded
from .utility import image_alpha, file_resource, copy_graphic_area, gprint
from .utility import set_active_object, set_cursor, add, set_backdrop
# import GuiManager and controls into this package's namespace
from .guimanager import GuiManager, GKind
from .widgets.frame import Frame, State
from .widgets.label import Label
from .widgets.button import Button
from .widgets.scrollbar import Scrollbar
from .widgets.pushbuttongroup import PushButtonGroup
from .widgets.image import Image
from .widgets.togglebutton import ToggleButton
from .forms.window import Window
# fix font graphical scaling issues with Windows
if os.name == 'nt':
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
