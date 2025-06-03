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
    from .guimanager import GuiManager
    gui = GuiManager()
    if window != None:
        x, y = gui.lock_area(point)
        wx, wy = window.x, window.y
        return (x - wx, y - wy)
    # conversion not necessary
    return gui.lock_area(point)

# convert the point from a window point to a main surface one
def convert_to_screen(point, window):
    # fall-through function, perform the conversion only if necessary
    from .guimanager import GuiManager
    gui = GuiManager()
    if window != None:
        x, y = point
        wx, wy = window.x, window.y
        return gui.lock_area((x + wx, y + wy))
    # conversion not necessary
    return gui.lock_area(point)

def set_active_object(object=None):
    from .guimanager import GuiManager
    gui = GuiManager()
    # set which object is active
    gui.active_object = object

def set_cursor(hotspot, *image):
    from .guimanager import GuiManager
    gui = GuiManager()
    # set the cursor image and hotspot
    gui.cursor_image = image_alpha('cursors', *image)
    gui.cursor_rect = gui.cursor_image.get_rect()
    gui.cursor_hotspot = hotspot

def gui_init(screen):
    # create a gui manager and set the screen for it
    from .guimanager import GuiManager
    gui = GuiManager()
    set_surface(screen)
    return gui

def add(widget, callback=None):
    from .guimanager import GuiManager
    gui = GuiManager()
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

# active window bank
window_bank = None
def window(title, pos, size, backdrop=None):
    # the purpose of this manipulator instead of calling Window directly
    # is so that extra information like the window bank can be used.
    # window constructor, return the window object if it is needed
    global window_bank
    from .forms.window import Window
    return Window(title, pos, size, backdrop)

def set_surface(surface):
    # set the surface the gui manager draws to
    from .guimanager import GuiManager
    gui = GuiManager()
    gui.surface = surface

def set_backdrop(image, obj=None):
    # set the backdrop bitmap for the main surface and copy it to the pristine bitmap
    from .guimanager import GuiManager
    gui = GuiManager()
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
    from .guimanager import GuiManager
    gui = GuiManager()
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
    from .guimanager import GuiManager
    gui = GuiManager()
    if obj == None:
        obj = gui
    if area == None:
        area = obj.pristine.get_rect()
    x, y, _, _ = area
    obj.surface.blit(obj.pristine, (x, y), area)
