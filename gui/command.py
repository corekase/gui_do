import os
import pygame
from pygame import Rect
from .constants import colours

# filename helper
def file_resource(*names):
    # return an os-independent filename inside data path
    return os.path.join('data', *names)

# alpha image loading
def image_alpha(*names):
    # load, convert with an alpha channel, and return an image surface
    return pygame.image.load(file_resource(*names)).convert_alpha()

# layout helper
def centre(bigger, smaller):
    # helper function that returns a centred position
    return int((bigger / 2) - (smaller / 2))

# gridded layout variables and functions
position_gridded = x_size_pixels_gridded = y_size_pixels_gridded = space_size_gridded = use_rect = None

# setup variables for gridded
def set_grid_properties(anchor, width, height, spacing, use_rect_flag=True):
    global position_gridded, x_size_pixels_gridded, y_size_pixels_gridded, space_size_gridded, use_rect
    position_gridded = anchor
    x_size_pixels_gridded = width
    y_size_pixels_gridded = height
    space_size_gridded = spacing
    use_rect = use_rect_flag

# returns Rect() from width, height, and spacing for x and y grid coordinates from the anchor
def gridded(x, y):
    base_x, base_y = position_gridded
    # (size per unit) + (space per unit)
    x_pos = base_x + (x * x_size_pixels_gridded) + (x * space_size_gridded)
    y_pos = base_y + (y * y_size_pixels_gridded) + (y * space_size_gridded)
    if use_rect:
        return Rect(x_pos, y_pos, x_size_pixels_gridded, y_size_pixels_gridded)
    else:
        return (x_pos, y_pos)

# current font object
font_object = None
# key:value -> key, name of font and value, font object
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

# render text with or without a shadow
def render_text(text, colour=colours['text'], shadow=False, shadow_colour=colours['none']):
    # return a bitmap of the text and a shadow of given colours
    text_bitmap = font_object.render(text, True, colour, None)
    text_rect = text_bitmap.get_rect()
    w, h = text_rect.width, text_rect.height
    if shadow:
        w += 1
        h += 1
    bitmap = pygame.Surface((w, h), pygame.SRCALPHA)
    if shadow:
        shadow_bitmap = font_object.render(text, True, shadow_colour, None)
        bitmap.blit(shadow_bitmap, (1, 1))
    bitmap.blit(text_bitmap, (0, 0))
    return bitmap
