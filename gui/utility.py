# utility is a module
# the first time utility is imported from anywhere its namespace is initialized, every
# subsequent import anywhere else reuses the namespace - intialization happens only once
import os
import pygame
from pygame import Rect
from .widget import colours

# reference to current font object
font_object = None
# key:value -> key, name of font. value, font object
fonts = {}

def load_font(name, font, size):
    fonts[name] = pygame.font.Font(file_resource('fonts', font), size)

def set_font(name):
    global font_object
    font_object = fonts[name]

def gprint(screen, text, position):
    bitmap = render_text(text)
    screen.blit(bitmap, position)

# gridded layout variables and functions
position_gridded = x_size_pixels_gridded = y_size_pixels_gridded = space_size_gridded = None

def set_anchor(pos):
    # set the origin of gridded locations
    global position_gridded
    position_gridded = pos

def set_width(x_pixels):
    # set x size of gridded location in pixels
    global x_size_pixels_gridded
    x_size_pixels_gridded = x_pixels

def set_height(y_pixels):
    # set y size of gridded location in pixels
    global y_size_pixels_gridded
    y_size_pixels_gridded = y_pixels

def set_spacing(spacing):
    # set spacing between gridded locations in pixels
    global space_size_gridded
    space_size_gridded = spacing

def set_grid_properties(anchor, width, height, spacing):
    # set all the properties at once
    global position_gridded, x_size_pixels_gridded, y_size_pixels_gridded, space_size_gridded
    position_gridded = anchor
    x_size_pixels_gridded = width
    y_size_pixels_gridded = height
    space_size_gridded = spacing

def gridded(x, y):
    # returns Rect() from width, height, and spacing for x and y grid coordinates from the anchor
    base_x, base_y = position_gridded
    x_location = (x * x_size_pixels_gridded) + (space_size_gridded * x)
    y_location = (y * y_size_pixels_gridded) + (space_size_gridded * y) + (y * 1)
    return Rect(base_x + x_location, base_y + y_location, x_size_pixels_gridded, y_size_pixels_gridded)

# -> To-do: make tile_images a dictionary of dictionaries to add support for multiple
#           tile image sets while still working within as a static module.  The first dictionary
#           is names for keys, and each names value is another dictionary of tile images.
#           Each named set stores a variable tile size and they do not have to be the same.
# tile sheet tiles are cut out of
tiles = None
# graphic size of tiles, squared
tile_size = 32
# dictionary to cache images so one surface for one tile position and reused on later calls
tile_images = {}

def cut(surface, rect, flags = 0):
    bitmap = pygame.Surface((rect.width, rect.height), flags)
    bitmap.blit(surface, (0, 0), rect)
    return bitmap

def cut_tile(tile):
    # if the tile is cached return that otherwise create the graphic image and cache it
    if tile not in tile_images.keys():
        x, y = tile
        surface = cut(tiles, Rect(x * tile_size, y * tile_size, tile_size, tile_size), pygame.SRCALPHA)
        tile_images[tile] = surface
    return tile_images[tile]

def image_alpha(*names):
    # load, convert with an alpha channel, and return an image surface
    return pygame.image.load(file_resource(*names)).convert_alpha()

def file_resource(*names):
    # return an os-independent filename inside data path
    return os.path.join('data', *names)

# -> To-do: make padding functions for buttons. uses set_font state, make a "get_button_height" for the text
#           size of that font, make a "grid" that takes x and y in button layout coordinates and returns
#           graphical x and y taking into account button width and height also based on current set_font
#    then, grid layouts of buttons are simple

def padding(line, size):
    # text layout helper function
    # return = base + line height + spacer size
    return 1 + (line * size) + (line * 2)

def render_text(text, highlight=False):
    # render helper function so same values aren't repeated
    if highlight:
        colour = colours['highlight']
    else:
        colour = colours['text']
    # return a bitmap of the chosen colour
    return font_object.render(text, True, colour)

def centre(bigger, smaller):
    # helper function that returns a centred position
    return int((bigger / 2) - (smaller / 2))
