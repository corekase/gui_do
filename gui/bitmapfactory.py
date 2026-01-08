import pygame
from math import cos, sin, radians
from pygame.surface import Surface
from pygame.surfarray import blit_array
from pygame import Rect, PixelArray
from pygame.draw import rect, line, polygon, circle
from pygame.transform import rotate, smoothscale
from .command import set_font, set_last_font, render_text_shadow, centre
from .widgets.widget import colours

class BitmapFactory:
    # the following code makes the BitmapFactory a singleton.
    # No matter how many times it is instantiated the result is the one object and its state
    _instance_ = None
    def __new__(cls):
        if BitmapFactory._instance_ is None:
            BitmapFactory._instance_ = object.__new__(cls)
            BitmapFactory._instance_._populate_()
        return BitmapFactory._instance_

    # instead of an __init__ we have _populate_ and it is executed exactly once
    def _populate_(self):
        #
        #
        # in the bitmapfactory implement a 'theme bank' like how the gui will be
        # implementing an object bank. the factory really just returns bitmaps so
        # as gtk2 theme support develops this is where bitmaps for gui objects will
        # be made and returned to the gui_do gui code.
        #
        #   theme_bank[theme]['bitmaps'] = {}
        #   theme_bank[theme]['needed_list'] = []
        #   ..and so on for more theme keys
        #    -> theme_bank is a dict of themes which each contain a dict where 'bitmaps'
        #       is a key which is a dict of needed items. the theme key can also contain
        #       other needed items in addition to the 'bitmaps' key
        #
        # the bitmapfactory takes requests for bitmaps for specific kinds of widgets.
        # then, when the request gets here, depending on self.theme, either the built-in
        # theme is used, the only one so far, or the contents of theme_bank[theme]['bitmaps']
        # are used to construct the bitmaps returned to gui_do. and gui_do is all bitmaps so it
        # is theme-agnostic
        #
        #
        self.theme = 'built_in'

    def set_theme(self, theme):
        # the current theme which controls which bitmaps are being rendered and returned to
        # client widgets. when generating bitmaps the current theme is tried first, and if
        # the definition to construct a bitmap isn't implemented yet - loading of gtk2 themes,
        # then fall-back to the built-in theme.
        #
        # -> try to construct from self.theme, if any element is not implemented in gtk2 bitmap
        #    loading and parsing functions then use the built_in generator instead
        self.theme = theme

    def draw_window_title_bar_bitmaps(self, title, width, size):
        saved = []
        saved.append(self.draw_window_title_bar_bitmap(title, width, size, colours['full']))
        saved.append(self.draw_window_title_bar_bitmap(title, width, size, colours['highlight']))
        return saved

    def draw_window_title_bar_bitmap(self, title, width, size, colour=None):
        from .widgets.frame import Frame, FrState
        set_font('titlebar')
        if colour == None:
            colour = colours['highlight']
        title_surface = Surface((width, size)).convert()
        frame = Frame('titlebar_frame', Rect(0, 0, width, size))
        frame.state = FrState.Armed
        frame.surface = title_surface
        frame.draw()
        text = render_text_shadow(title, colour)
        text_y = centre(size, text.get_rect().height)
        title_surface.blit(text, (5, text_y + 1))
        set_last_font()
        return title_surface

    def draw_window_lower_widget_bitmap(self, size, col1, col2):
        surface = Surface((size, size), pygame.SRCALPHA).convert_alpha()
        panel_size = (size - 6) // 2
        offset = (size - 6) // 4
        base = centre(size, (panel_size + offset)) - 3
        panel1 = Rect(base + 3, base, panel_size, panel_size)
        panel2 = Rect(base + panel_size - offset + 3, base + panel_size - offset, panel_size, panel_size)
        rect(surface, col1, panel1)
        rect(surface, colours['none'], panel1, 1)
        rect(surface, col2, panel2)
        rect(surface, colours['none'], panel2, 1)
        return surface

    def draw_box_bitmaps(self, text, rect):
        _, _, w, h = rect
        saved = []
        text_bitmap = render_text_shadow(text)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        idle_surface = Surface((w, h)).convert()
        self.draw_box_state(idle_surface, 'idle')
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        hover_surface = Surface((w, h)).convert()
        self.draw_box_state(hover_surface, 'hover')
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text_shadow(text, colours['highlight'])
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        armed_surface = Surface((w, h)).convert()
        self.draw_box_state(armed_surface, 'armed')
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        return saved

    def draw_box_state(self, surface, state):
        if state == 'idle':
            self.draw_box_bitmap(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['medium'])
        elif state == 'hover':
            self.draw_box_bitmap(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['light'])
        elif state == 'armed':
            self.draw_box_bitmap(surface, colours['none'], colours['light'], colours['none'], colours['full'], colours['dark'])

    def draw_box_bitmap(self, surface, ul, lr, ul_d, lr_d, background):
        # ul, lr = upper and left, lower and right lines
        # ul_d, lr_d = upper-left dot, lower-right dot
        # get positions and sizes
        _, _, width, height = surface.get_rect()
        x = y = 0
        # lock surface for drawing
        surface.lock()
        # draw background
        rect(surface, background, surface.get_rect(), 0)
        # draw frame upper and left lines
        line(surface, ul, (x, y), (x + width - 1, y))
        line(surface, ul, (x, y), (x, y + height - 1))
        # draw frame lower and right lines
        line(surface, lr, (x, y + height - 1), (x + width - 1, y + height - 1))
        line(surface, lr, (x + width - 1, y - 1), (x + width - 1, y + height - 1))
        # plot upper left dot
        surface.set_at((x + 1, y + 1), ul_d)
        # plot lower right dot
        surface.set_at((x + width - 2, y + height - 2), lr_d)
        # unlock surface
        surface.unlock()

    def draw_button_bitmaps(self, text, rect):
        _, _, w, h = rect
        saved = []
        text_bitmap = render_text_shadow(text)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        idle_surface = Surface((w, h), pygame.SRCALPHA).convert_alpha()
        self.draw_button_state(idle_surface, 'idle')
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        hover_surface = Surface((w, h), pygame.SRCALPHA).convert_alpha()
        self.draw_button_state(hover_surface, 'hover')
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text_shadow(text, colours['highlight'])
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        armed_surface = Surface((w, h), pygame.SRCALPHA).convert_alpha()
        self.draw_button_state(armed_surface, 'armed')
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        return saved

    def draw_button_state(self, surface, state):
        if state == 'idle':
            self.draw_round_frame_bitmap(surface, colours['light'], colours['medium'])
        elif state == 'hover':
            self.draw_round_frame_bitmap(surface, colours['light'], colours['light'])
        elif state == 'armed':
            self.draw_round_frame_bitmap(surface, colours['none'], colours['dark'])

    def draw_round_frame_bitmap(self, surface, border, background):
        _, _, w, h = surface.get_rect()
        radius = h // 4
        circle(surface, border, (radius, radius), radius, 1, draw_top_left=True)
        circle(surface, border, (w - radius, radius), radius, 1, draw_top_right=True)
        line(surface, border, (radius, 0), (w - radius, 0), 1)
        circle(surface, border, (radius, h - radius), radius, 1, draw_bottom_left=True)
        circle(surface, border, (w - radius, h - radius), radius, 1, draw_bottom_right=True)
        line(surface, border, (radius, h - 1), (w - radius, h - 1), 1)
        line(surface, border, (0, radius), (0, h - radius), 1)
        line(surface, border, (w - 1, radius), (w - 1, h - radius), 1)
        self.flood_fill(surface, (w // 2, h // 2), background)

    def flood_fill(self, surface, position, color):
        # convert the surface to an array
        pixels = PixelArray(surface)
        # convert the fill color to integer representation
        new_color = surface.map_rgb(color)
        # read the color to replace from the starting position
        old_color = pixels[position]
        # begin a queue with the starting position
        locations = [position]
        while len(locations) > 0:
            # pop a position from the queue
            x, y = locations.pop()
            try:
                if pixels[x, y] != old_color:
                    # if it isn't the old color then skip the position
                    continue
            except IndexError:
                # outside of the pixel array
                continue
            # it is the old color and within the array, replace color
            pixels[x, y] = new_color
            # add neighbors to the queue
            locations.append((x + 1, y))
            locations.append((x - 1, y))
            locations.append((x, y + 1))
            locations.append((x, y - 1))
        # convert the array back into the surface
        blit_array(surface, pixels)
        # delete the array because it implicitly affects locks/unlocks of the surface
        del pixels

    def get_pushbutton_style_bitmaps(self, style, text, rect):
        if style == 0:
            return self.draw_box_bitmaps(text, rect)
        elif style == 1:
            return self.draw_radio_pushbutton_bitmaps(text)
        else:
            raise Exception(f'style index {style} not implemented')

    def draw_radio_pushbutton_bitmaps(self, text):
        idle_bitmap = self.draw_radio_pushbutton_bitmap(text, colours['light'], colours['dark'])
        hover_bitmap = self.draw_radio_pushbutton_bitmap(text, colours['highlight'], colours['dark'])
        armed_bitmap = self.draw_radio_pushbutton_bitmap(text, colours['highlight'], colours['dark'])
        return idle_bitmap, hover_bitmap, armed_bitmap

    def draw_radio_pushbutton_bitmap(self, text, col1, col2):
        text_bitmap = render_text_shadow(text)
        text_height = text_bitmap.get_rect().height
        radio_bitmap = self.draw_radio_bitmap(int(text_height / 1.8), col1, col2)
        x_size = text_height + text_bitmap.get_rect().width
        button_complete = Surface((x_size, text_height), pygame.SRCALPHA).convert_alpha()
        button_complete.blit(radio_bitmap, (0, centre(text_height, radio_bitmap.get_rect().height)))
        button_complete.blit(text_bitmap, (radio_bitmap.get_rect().width + 2, 0))
        return button_complete

    def draw_radio_bitmap(self, diameter, col1, col2):
        radio_bitmap = Surface((diameter, diameter), pygame.SRCALPHA).convert_alpha()
        radius = diameter // 2
        circle(radio_bitmap, col2, (radius, radius), radius, 1)
        self.flood_fill(radio_bitmap, (radius, radius), col1)
        return radio_bitmap

    def draw_arrow_state_bitmaps(self, rect, direction):
        # draw idle, hover, and armed bitmaps for the passed direction
        # and return a list of those three
        states = self.draw_frame_bitmaps(rect)
        glyph_set = []
        if rect.width <= rect.height:
            size = rect.width
        else:
            size = rect.height
        # create a polygon for the glyph then draw it in full colour filled
        # then draw the polygon again in none colour 1 pixel outline
        glyph = Surface((400, 400), pygame.SRCALPHA).convert_alpha()
        # draw polygon
        points = ((350, 200), (100, 350), (100, 240), (50, 240), (50, 160), (100, 160), (100, 50), (350, 200))
        polygon(glyph, colours['full'], points, 0)
        polygon(glyph, colours['none'], points, 20)
        # rotate polygon to direction
        glyph = rotate(glyph, direction)
        # scale polygon to bitmap size
        glyph = smoothscale(glyph, (size, size))
        # centre the glyph in the state bitmap area
        glyph_x = centre(rect.width, size)
        glyph_y = centre(rect.height, size)
        # draw each state with the glyph
        for state in states:
            # for each state of the frame bitmap add a glyph bitmap over it
            state.blit(glyph, (glyph_x, glyph_y))
            glyph_set.append(state)
        return glyph_set

    def draw_frame_bitmaps(self, rect):
        _, _, w, h = rect
        saved = []
        idle_surface = Surface((w, h)).convert()
        self.draw_box_state(idle_surface, 'idle')
        saved.append(idle_surface)
        hover_surface = Surface((w, h)).convert()
        self.draw_box_state(hover_surface, 'hover')
        saved.append(hover_surface)
        armed_surface = Surface((w, h)).convert()
        self.draw_box_state(armed_surface, 'armed')
        saved.append(armed_surface)
        return saved
