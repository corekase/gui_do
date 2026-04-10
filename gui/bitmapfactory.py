import pygame
from math import cos, sin, radians
from pygame.surface import Surface
from pygame.surfarray import blit_array
from collections import deque
from pygame import Rect, PixelArray, SRCALPHA
from pygame.draw import rect, line, polygon, circle
from pygame.transform import rotate, smoothscale
from .command import set_font, set_last_font, render_text, centre
from .constants import colours, BtnStyl

class BitmapFactory:
    # the following code makes the BitmapFactory a singleton.
    # No matter how many times it is instantiated the result is the one object and its state
    _instance_ = None
    def __new__(cls):
        if BitmapFactory._instance_ is None:
            BitmapFactory._instance_ = object.__new__(cls)
        return BitmapFactory._instance_

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
        text = render_text(title, colour, True)
        text_y = centre(size, text.get_rect().height)
        title_surface.blit(text, (5, text_y))
        set_last_font()
        return title_surface

    def draw_window_lower_widget_bitmap(self, size, col1, col2):
        surface = Surface((size, size), SRCALPHA).convert_alpha()
        self.draw_box_bitmaps(surface, 'idle')
        gutter = int(size * 0.1) // 2
        panel_size = int(size * 0.45)
        offset = int(size * 0.2)
        offsetb = offset // 2
        base = centre(size, (panel_size + offset))
        panel1 = Rect(base, base - gutter, panel_size + offsetb, panel_size + gutter + offsetb)
        panel2 = Rect(base + offset, base + gutter + offsetb, panel_size + offsetb, panel_size + gutter + offsetb)
        rect(surface, col1, panel1)
        rect(surface, colours['none'], panel1, 1)
        rect(surface, col2, panel2)
        rect(surface, colours['none'], panel2, 1)
        return surface

    def draw_frame_bitmaps(self, rect):
        _, _, w, h = rect
        saved = []
        idle_surface = Surface((w, h)).convert()
        self.draw_box_bitmaps(idle_surface, 'idle')
        saved.append(idle_surface)
        hover_surface = Surface((w, h)).convert()
        self.draw_box_bitmaps(hover_surface, 'hover')
        saved.append(hover_surface)
        armed_surface = Surface((w, h)).convert()
        self.draw_box_bitmaps(armed_surface, 'armed')
        saved.append(armed_surface)
        return saved

    def get_styled_bitmaps(self, style, text, rect):
        if style == BtnStyl.Boxed:
            return self.draw_box_style_bitmaps(text, rect)
        elif style == BtnStyl.Rounded:
            return self.draw_rounded_style_bitmaps(text, rect)
        elif style == BtnStyl.Angled:
            return self.draw_angle_style_bitmaps(text, rect)
        elif style == BtnStyl.Radio:
            return self.draw_radio_style_bitmaps(text, rect)
        elif style == BtnStyl.Check:
            return self.draw_check_style_bitmaps(text, rect)
        else:
            from .guimanager import GuiError
            raise GuiError('style not implemented')

    def draw_box_style_bitmaps(self, text, rect):
        _, _, w, h = rect
        saved = []
        text_bitmap = render_text(text, colours['text'], True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        idle_surface = Surface((w, h)).convert()
        self.draw_box_bitmaps(idle_surface, 'idle')
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        hover_surface = Surface((w, h)).convert()
        self.draw_box_bitmaps(hover_surface, 'hover')
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text(text, colours['highlight'], True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        armed_surface = Surface((w, h)).convert()
        self.draw_box_bitmaps(armed_surface, 'armed')
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        return saved, rect

    def draw_box_bitmaps(self, surface, state):
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

    def draw_radio_style_bitmaps(self, text, rect):
        idle_bitmap, idle_rect = self.draw_radio_style_bitmap(rect, text, colours['light'], colours['dark'])
        hover_bitmap, _ = self.draw_radio_style_bitmap(rect, text, colours['full'], colours['none'])
        armed_bitmap, _ = self.draw_radio_style_bitmap(rect, text, colours['highlight'], colours['dark'])
        return (idle_bitmap, hover_bitmap, armed_bitmap), idle_rect

    def draw_radio_style_bitmap(self, rect, text, col1, col2):
        text_bitmap = render_text(text, colours['text'], True)
        _, _, text_width, text_height = text_bitmap.get_rect()
        gutter = int(text_height * 0.1)
        radio_bitmap = self.draw_radio_bitmap(text_height, col1, col2)
        button_complete = Surface((rect.width, rect.height), SRCALPHA).convert_alpha()
        y_offset = centre(rect.height, text_height)
        button_complete.blit(radio_bitmap, (0, y_offset))
        button_complete.blit(text_bitmap, (radio_bitmap.get_rect().width + 2, y_offset))
        return button_complete, Rect(rect.x + gutter, rect.y + y_offset, text_height + text_width + gutter, text_height)

    def draw_radio_bitmap(self, size, col1, col2):
        radio_bitmap = Surface((400, 400), SRCALPHA).convert_alpha()
        centre_point = 200
        radius = 128
        points = []
        for point in range(0, 360, 5):
            x1 = int(round(radius * cos(radians(point))))
            y1 = int(round(radius * sin(radians(point))))
            points.append((centre_point + x1, centre_point + y1))
        polygon(radio_bitmap, col1, points, 0)
        polygon(radio_bitmap, col2, points, 24)
        radio_bitmap = smoothscale(radio_bitmap, (size, size))
        return radio_bitmap

    def draw_check_style_bitmaps(self, text, rect):
        idle_bitmap, hit_rect = self.draw_check_style_bitmap(rect, 0, text)
        hover_bitmap, _ = self.draw_check_style_bitmap(rect, 1, text)
        armed_bitmap, _ = self.draw_check_style_bitmap(rect, 2, text)
        return (idle_bitmap, hover_bitmap, armed_bitmap), hit_rect

    def draw_check_style_bitmap(self, rect, state, text):
        text_bitmap = render_text(text, colours['text'], True)
        _, _, text_width, text_height = text_bitmap.get_rect()
        check_bitmap = self.draw_check_bitmap(state, text_height)
        y_offset = centre(rect.height, text_height)
        gutter = int(text_height * 0.1)
        x_size = text_height + text_width
        button_complete = Surface((rect.width, rect.height), SRCALPHA).convert_alpha()
        button_complete.blit(check_bitmap, (0, y_offset))
        button_complete.blit(text_bitmap, (text_height + 2, y_offset))
        return button_complete, Rect(rect.x + gutter, rect.y + y_offset, x_size + gutter, text_height)

    def draw_check_bitmap(self, state, size):
        shrink = size * 0.65
        offset = int(centre(size, shrink))
        box_bitmap = Surface((int(shrink), int(shrink))).convert()
        check_bitmap = Surface((size, size), SRCALPHA).convert_alpha()
        if state == 0:
            self.draw_box_bitmaps(box_bitmap, 'idle')
        elif state == 1:
            self.draw_box_bitmaps(box_bitmap, 'hover')
        elif state == 2:
            self.draw_box_bitmaps(box_bitmap, 'armed')
        check_bitmap.blit(box_bitmap, (offset, offset))
        if state == 1 or state == 2:
            glyph = Surface((400, 400), SRCALPHA).convert_alpha()
            points = ((20, 200), (80, 140), (160, 220), (360, 0), (400, 60), (160, 320), (20, 200))
            polygon(glyph, colours['full'], points, 0)
            polygon(glyph, colours['none'], points, 20)
            glyph = smoothscale(glyph, (size, size))
            check_bitmap.blit(glyph, (0, 0))
        return check_bitmap

    def draw_rounded_style_bitmaps(self, text, rect):
        _, _, w, h = rect
        saved = []
        text_bitmap = render_text(text, colours['text'], True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        idle_surface = Surface((w, h), SRCALPHA).convert_alpha()
        self.draw_rounded_state(idle_surface, 'idle')
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        hover_surface = Surface((w, h), SRCALPHA).convert_alpha()
        self.draw_rounded_state(hover_surface, 'hover')
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text(text, colours['highlight'], True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        armed_surface = Surface((w, h), SRCALPHA).convert_alpha()
        self.draw_rounded_state(armed_surface, 'armed')
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        return saved, rect

    def draw_rounded_state(self, surface, state):
        if state == 'idle':
            self.draw_round_style_bitmap(surface, colours['light'], colours['medium'])
        elif state == 'hover':
            self.draw_round_style_bitmap(surface, colours['light'], colours['light'])
        elif state == 'armed':
            self.draw_round_style_bitmap(surface, colours['none'], colours['dark'])

    def draw_round_style_bitmap(self, surface, border, background):
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

    def draw_angle_style_bitmaps(self, text, rect):
        _, _, w, h = rect
        saved = []
        text_bitmap = render_text(text, colours['text'], True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        idle_surface = self.draw_angle_state((w, h), 'idle')
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        hover_surface = self.draw_angle_state((w, h), 'hover')
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text(text, colours['highlight'], True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        armed_surface = self.draw_angle_state((w, h), 'armed')
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        return saved, rect

    def draw_angle_state(self, size, state):
        if state == 'idle':
            return self.draw_angle_style_bitmap(size, colours['light'], colours['medium'])
        elif state == 'hover':
            return self.draw_angle_style_bitmap(size, colours['light'], colours['light'])
        elif state == 'armed':
            return self.draw_angle_style_bitmap(size, colours['none'], colours['dark'])

    def draw_angle_style_bitmap(self, size, border, background):
        w_surface, h_surface = size
        angle_bitmap = Surface((w_surface * 10, h_surface * 10), SRCALPHA).convert_alpha()
        _, _, w, h = angle_bitmap.get_rect()
        dist = h // 3
        points = ((dist, 0), (w - dist, 0), (w - 1, dist), (w - 1, h - dist - 1), (w - dist, h - 1), (dist, h - 1), (0, h - dist), (0, dist), (dist, 0))
        polygon(angle_bitmap, background, points, 0)
        polygon(angle_bitmap, border, points, dist // 4)
        return smoothscale(angle_bitmap, (w_surface, h_surface))

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
        glyph = Surface((400, 400), SRCALPHA).convert_alpha()
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

    def flood_fill(self, surface, position, colour):
        # convert the surface to an array
        pixels = PixelArray(surface)
        # convert the fill color to integer representation
        new_colour = surface.map_rgb(colour)
        # read the color to replace from the starting position
        old_colour = pixels[position]
        # fill start position is already the fill colour
        if old_colour == new_colour:
            del pixels
            return
        width, height = surface.get_size()
        locations = deque([position])
        while locations:
            # pop a position from the queue
            x, y = locations.popleft()
            # if the old color and within the array, replace color
            if pixels[x, y] == old_colour:
                pixels[x, y] = new_colour
                # add neighbors to the queue
                if x > 0: locations.append((x - 1, y))
                if x < width - 1: locations.append((x + 1, y))
                if y > 0: locations.append((x, y - 1))
                if y < height - 1: locations.append((x, y + 1))
        # convert the array back into the surface
        blit_array(surface, pixels)
        # delete the array because it implicitly affects locks/unlocks of the surface
        del pixels
