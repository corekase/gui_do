# utility is a module
# the first time utility is imported from anywhere its namespace is initialized, every
# subsequent import anywhere else reuses the namespace - intialization happens only once
import os
import pygame
from pygame import Rect
from .widget import colours

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

# graphical print function
def gprint(screen, text, position):
    bitmap = render_text(text)
    screen.blit(bitmap, (position[0], position[1]))

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

# graphic cut helper
def cut(surface, rect, flags = 0):
    bitmap = pygame.Surface((rect.width, rect.height), flags)
    bitmap.blit(surface, (0, 0), rect)
    return bitmap

# convert mouse position to a window position
def screen_to_window(point, window):
    x, y = point
    wx, wy = window.x, window.y
    return (x - wx, y - wy)

def window_to_screen(point, window):
    x, y = point
    wx, wy = window.x, window.y
    return (x + wx, y + wy)
