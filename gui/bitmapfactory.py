import pygame
from math import cos, sin, radians
from pygame import Rect
from pygame.draw import rect, line
from .command import set_font, set_last_font, render_text, centre
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
        saved.append(self.draw_window_title_bar_bitmap(title, width, size, False))
        saved.append(self.draw_window_title_bar_bitmap(title, width, size, True))
        return saved

    def draw_window_title_bar_bitmap(self, title, width, size, highlight=False):
        from .widgets.frame import Frame, FrState
        set_font('titlebar')
        text_bitmap = render_text(title, highlight)
        title_surface = pygame.surface.Surface((width, size)).convert()
        frame = Frame('titlebar_frame', Rect(0, 0, width, size))
        frame.state = FrState.Armed
        frame.surface = title_surface
        frame.draw()
        title_surface.blit(text_bitmap, (4, 4))
        set_last_font()
        return title_surface

    def draw_window_lower_widget_bitmap(self, size, col1, col2):
        surface = pygame.surface.Surface((size, size), pygame.SRCALPHA)
        rect(surface, col1, Rect(3, 3, 9, 9))
        rect(surface, colours['none'], Rect(3, 3, 9, 9), 1)
        rect(surface, col2, Rect(6, 6, 9, 9))
        rect(surface, colours['none'], Rect(6, 6, 9, 9), 1)
        return surface

    def get_pushbutton_style_bitmaps(self, style, text, rect):
        if style == 0:
            return self.draw_box_button_bitmaps(text, rect)
        elif style == 1:
            return self.draw_radio_pushbutton_bitmaps(text)
        else:
            raise Exception(f'style index {style} not implemented')

    def draw_box_button_bitmaps(self, text, rect):
        _, _, w, h = rect
        saved = []
        text_bitmap = render_text(text)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height) - 1
        idle_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_frame_state_bitmap(idle_surface, 'idle', Rect(0, 0, w, h), colours)
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        text_bitmap = render_text(text)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height) - 1
        hover_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_frame_state_bitmap(hover_surface, 'hover', Rect(0, 0, w, h), colours)
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text(text, True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height) - 1
        armed_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_frame_state_bitmap(armed_surface, 'armed', Rect(0, 0, w, h), colours)
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        return saved

    def draw_radio_pushbutton_bitmaps(self, text):
        idle_bitmap = self.draw_radio_pushbutton_bitmap(text, colours['light'], colours['dark'])
        hover_bitmap = self.draw_radio_pushbutton_bitmap(text, colours['highlight'], colours['dark'])
        armed_bitmap = self.draw_radio_pushbutton_bitmap(text, colours['highlight'], colours['dark'])
        return idle_bitmap, hover_bitmap, armed_bitmap

    def draw_radio_pushbutton_bitmap(self, text, col1, col2, highlight=False):
        text_bitmap = render_text(text, highlight)
        text_height = text_bitmap.get_rect().height
        radio_bitmap = self.draw_radio_checked_bitmap((text_height // 2) + 1, col1, col2)
        x_size = text_height + text_bitmap.get_rect().width
        button_complete = pygame.surface.Surface((x_size, text_height), pygame.SRCALPHA)
        button_complete.blit(radio_bitmap, (0, centre(text_height, radio_bitmap.get_rect().height) + 4))
        button_complete.blit(text_bitmap, ((text_height // 2) + 4, 2))
        return button_complete

    def draw_radio_checked_bitmap(self, diameter, col1, col2):
        # separate out from draw_radio_pushbutton_bitmap so the same bitmap can be used
        # in a checkbox too
        radio_bitmap = pygame.surface.Surface((400, 400), pygame.SRCALPHA)
        radius = 200
        points = []
        for point in range(0, 360, 5):
            x1 = int(round(radius * cos(radians(point))))
            y1 = int(round(radius * sin(radians(point))))
            points.append((radius + x1, radius + y1))
        pygame.draw.polygon(radio_bitmap, col1, points, 0)
        pygame.draw.polygon(radio_bitmap, col2, points, 90)
        radio_bitmap = pygame.transform.smoothscale(radio_bitmap, (diameter, diameter))
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
        glyph = pygame.surface.Surface((400, 400), pygame.SRCALPHA)
        # draw polygon
        points = ((350, 200), (100, 350), (100, 240), (50, 240), (50, 160), (100, 160), (100, 50), (350, 200))
        pygame.draw.polygon(glyph, colours['full'], points, 0)
        pygame.draw.polygon(glyph, colours['none'], points, 20)
        # rotate polygon to direction
        glyph = pygame.transform.rotate(glyph, direction)
        # scale polygon to bitmap size
        glyph = pygame.transform.smoothscale(glyph, (size, size))
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
        x, y, w, h = rect
        saved = []
        idle_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_frame_state_bitmap(idle_surface, 'idle', Rect(0, 0, w, h), colours)
        saved.append(idle_surface)
        hover_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_frame_state_bitmap(hover_surface, 'hover', Rect(0, 0, w, h), colours)
        saved.append(hover_surface)
        armed_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_frame_state_bitmap(armed_surface, 'armed', Rect(0, 0, w, h), colours)
        saved.append(armed_surface)
        return saved

    def draw_frame_state_bitmap(self, surface, state, rect, colours):
        if state == 'idle':
            self.draw_base_frame_definition_bitmap(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['medium'], rect)
        elif state == 'hover':
            self.draw_base_frame_definition_bitmap(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['light'], rect)
        elif state == 'armed':
            self.draw_base_frame_definition_bitmap(surface, colours['none'], colours['light'], colours['none'], colours['full'], colours['dark'], rect)

    def draw_base_frame_definition_bitmap(self, surface, ul, lr, ul_d, lr_d, background, surface_rect):
        # ul, lr = upper and left, lower and right lines
        # ul_d, lr_d = upper-left dot, lower-right dot
        # get positions and sizes
        x, y, width, height = surface_rect
        # lock surface for drawing
        surface.lock()
        # draw background
        rect(surface, background, surface_rect, 0)
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
