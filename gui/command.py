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
    return font_object.render(text, True, colour, None)

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

# convert the point from a main surface one to a window point
def convert_to_window(point, window):
    # fall-through function, perform the conversion only if necessary
    if window != None:
        x, y = gui.lock_area(point)
        wx, wy = window.x, window.y
        return (x - wx, y - wy)
    # conversion not necessary
    return gui.lock_area(point)

# convert the point from a window point to a main surface one
def convert_to_screen(point, window):
    # fall-through function, perform the conversion only if necessary
    if window != None:
        x, y = point
        wx, wy = window.x, window.y
        return gui.lock_area((x + wx, y + wy))
    # conversion not necessary
    return gui.lock_area(point)

gui = None
def gui_init(screen):
    global gui
    # create a gui manager and set the screen for it
    from .guimanager import GuiManager
    gui = GuiManager()
    gui.surface = screen
    return gui

def set_buffered(buffered):
    # if buffered is set to True then bitmaps under gui objects
    # will be saved and the undraw will undo them
    # if buffered is set to False then no bitmaps are saved, the
    #   client doesn't call gui undraw, and instead they just
    #   clear their screen or other client logic and draw the gui
    #   again when they need it
    gui.buffered = buffered

def add(widget, callback=None):
    # give a reference to the gui
    widget.gui = gui
    # callback
    widget.callback = callback
    if gui.active_object != None:
        # store a reference to the window the widget is in
        widget.window = gui.active_object
        # give the widget a reference to the window surface
        widget.surface = gui.active_object.surface
        # append the widget to the window's list
        gui.active_object.widgets.append(widget)
    else:
        # give the widget a reference to the screen surface
        widget.surface = gui.surface
        # append the widget to the screen list
        gui.widgets.append(widget)
    return widget

def set_active_object(object=None):
    # set which object is active
    gui.active_object = object

# active window bank
window_bank = None
def Window(title, pos, size, backdrop=None):
    # window constructor
    # extra information like the window bank is added here
    global window_bank
    from .forms.window import WindowBase
    return WindowBase(title, pos, size, backdrop)

bank = None
def set_active_bank(dest_bank):
    # active bank manipulator, sets destination bank for add widget and window commands.
    # as items are added, their surfaces are still the screen or a window while they are being
    # instantiated. then loading and unloading just determine which are active at any given time
    global bank
    pass

def set_cursor(hotspot, *image):
    # set the cursor image and hotspot
    gui.cursor_image = image_alpha('cursors', *image)
    gui.cursor_rect = gui.cursor_image.get_rect()
    gui.cursor_hotspot = hotspot

def set_backdrop(image, obj=None):
    # set the backdrop bitmap for the main surface and copy it to the pristine bitmap
    if obj == None:
        obj = gui
    if image != None:
        data_path = os.path.join('data', 'images')
        bitmap = pygame.image.load(os.path.join(data_path, image))
        _, _, width, height = obj.surface.get_rect()
        scaled_bitmap = pygame.transform.smoothscale(bitmap, (width, height))
        obj.surface.blit(scaled_bitmap.convert(), (0, 0), scaled_bitmap.get_rect())
    else:
        raise Exception('set_backdrop() requires an image')
    obj.pristine = copy_graphic_area(obj.surface, obj.surface.get_rect()).convert()

def update_pristine(area=None, obj=None):
    # copy area from screen surface to the pristine surface
    # if area is None then update entire surface
    if obj == None:
        obj = gui
    if area == None:
        area = obj.surface.get_rect()
    x, y, _, _ = area
    obj.pristine.blit(obj.surface, (x, y), area)

def restore_pristine(area=None, obj=None):
    # if obj is ommited then restore_pristine is from the screen pristine.
    # if obj is supplied the object must have a obj.surface and an obj.pristine
    # to use here
    # restores a graphic area from the screen's pristine bitmap to the
    # screen surface. if area is None then restore entire surface
    if obj == None:
        obj = gui
    if area == None:
        area = obj.pristine.get_rect()
    x, y, _, _ = area
    obj.surface.blit(obj.pristine, (x, y), area)
