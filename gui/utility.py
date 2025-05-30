# utility is a module
import os
import pygame
from pygame import Rect
from .widgets.widget import colours

# font object variables and functions
# current font object
font_object = None
# key:value -> key, name of font. value, font object
fonts = {}

# load font
def load_font(name, font, size):
    fonts[name] = pygame.font.Font(file_resource('fonts', font), size)

# make a font active
last_font_object = None
def set_font(name):
    global font_object, last_font_object
    last_font_object = font_object
    font_object = fonts[name]

# restore the previous font
def set_last_font():
    global font_object
    font_object = last_font_object

# render text function
def render_text(text, highlight=False):
    if highlight:
        colour = colours['highlight']
    else:
        colour = colours['text']
    # return a bitmap of the chosen colour
    return font_object.render(text, True, colour)

# layout helper
def centre(bigger, smaller):
    # helper function that returns a centred position
    return int((bigger / 2) - (smaller / 2))

# gridded layout variables and functions
position_gridded = x_size_pixels_gridded = y_size_pixels_gridded = space_size_gridded = None

# setup variables for gridded
def set_grid_properties(anchor, width, height, spacing):
    global position_gridded, x_size_pixels_gridded, y_size_pixels_gridded, space_size_gridded
    position_gridded = anchor
    x_size_pixels_gridded = width
    y_size_pixels_gridded = height
    space_size_gridded = spacing

# returns Rect() from width, height, and spacing for x and y grid coordinates from the anchor
def gridded(x, y):
    base_x, base_y = position_gridded
    # (size per unit) + (space per unit) + (1 per unit, or another number)
    x_location = (x * x_size_pixels_gridded) + (x * space_size_gridded) + (x * 1)
    y_location = (y * y_size_pixels_gridded) + (y * space_size_gridded) + (y * 1)
    return Rect(base_x + x_location, base_y + y_location, x_size_pixels_gridded, y_size_pixels_gridded)

# alpha image loading
def image_alpha(*names):
    # load, convert with an alpha channel, and return an image surface
    return pygame.image.load(file_resource(*names)).convert_alpha()

# filename helper
def file_resource(*names):
    # return an os-independent filename inside data path
    return os.path.join('data', *names)

# copy graphic helper
def copy_graphic_area(surface, rect, flags = 0):
    bitmap = pygame.Surface((rect.width, rect.height), flags)
    bitmap.blit(surface, (0, 0), rect)
    return bitmap

# print to position helper
def gprint(screen, text, position, make_copy=False):
    bitmap = render_text(text)
    bitmap_rect = bitmap.get_rect()
    new_rect = Rect(position[0], position[1], bitmap_rect.width, bitmap_rect.height)
    if make_copy == True:
        saved = copy_graphic_area(screen, new_rect)
    screen.blit(bitmap, new_rect)
    if make_copy == True:
        return saved, new_rect
    return None, None

# convert the point from a main surface one to a window point
def convert_to_window(point, window):
    # fall-through function, perform the conversion only if necessary
    if window != None:
        x, y = point
        wx, wy = window.x, window.y
        return (x - wx, y - wy)
    # conversion not necessary
    return point

# convert the point from a window point to a main surface one
def convert_to_screen(point, window):
    # fall-through function, perform the conversion only if necessary
    if window != None:
        x, y = point
        wx, wy = window.x, window.y
        return (x + wx, y + wy)
    # conversion not necessary
    return point

def set_active_object(object=None):
    from .guimanager import GuiManager
    gui = GuiManager()
    # set which object is active
    gui.active_object = object

def set_cursor(hotspot, *image):
    from .guimanager import GuiManager
    gui = GuiManager()
    # set the cursor image and hotspot
    gui.cursor_image = image_alpha(*image)
    gui.cursor_rect = gui.cursor_image.get_rect()
    gui.cursor_hotspot = hotspot

def add(widget, callback=None):
    from .guimanager import GuiManager
    gui = GuiManager()
    widget.callback = callback
    # set_save manipulator controls this setting
    widget.save = gui.save
    if gui.active_object != None:
        widget.window = gui.active_object
        widget.surface = gui.active_object.surface
        # append the widget to the object
        gui.active_object.widgets.append(widget)
    else:
        # add a widget to the screen
        widget.gui = gui
        widget.surface = gui.surface
        # append the widget to the group
        gui.widgets.append(widget)
    return widget

def set_surface(surface):
    # set the surface the gui manager draws to
    from .guimanager import GuiManager
    gui = GuiManager()
    gui.surface = surface
