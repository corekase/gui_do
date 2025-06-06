# gui is a package
import os
# import utility functions into this package's namespace
from .command import gui_init, load_font, set_font, set_last_font, render_text, Window
from .command import centre, set_grid_properties, gridded
from .command import image_alpha, file_resource, copy_graphic_area
from .command import set_active_object, set_cursor, add, set_backdrop, update_pristine, restore_pristine
from .command import Scrollbar
# import GuiManager and widgets into this package's namespace
from .guimanager import GuiManager, GKind
from .widgets.widget import colours
from .widgets.frame import Frame, FrState
from .widgets.label import Label
from .widgets.button import Button
from .widgets.pushbuttongroup import PushButtonGroup
from .widgets.image import Image
from .widgets.togglebutton import ToggleButton
from .widgets.canvas import Canvas, CKind
# fix font graphical scaling issues with Windows
if os.name == 'nt':
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
