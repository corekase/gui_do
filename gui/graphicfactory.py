import pygame
from math import cos, sin, radians
from pygame import Rect
from pygame.draw import rect, line
from .utility import set_font, set_last_font, render_text, centre
from .widgets.widget import colours

class GraphicFactory:

    def draw_radio_graphic(self, text, rect):
        self.idle_bitmap = self.make_radio_button(text, rect, colours['light'], colours['dark'])
        self.hover_bitmap = self.make_radio_button(text, rect, colours['highlight'], colours['dark'])
        self.armed_bitmap = self.make_radio_button(text, rect, colours['highlight'], colours['dark'])
        return self.idle_bitmap, self.hover_bitmap, self.armed_bitmap

    def make_radio_button(self, text, rect, col1, col2, highlight=False):
        x, y, w, h = rect
        text_bitmap = render_text(text, highlight)
        text_height = text_bitmap.get_rect().height
        radio_bitmap = pygame.surface.Surface((text_height, text_height), pygame.SRCALPHA)
        y_offset = int(round(text_height / 2))
        radius = text_height / 4.0
        points = []
        for point in range(0, 360, 5):
            x1 = int(round(radius * cos(radians(point))))
            y1 = int(round(radius * sin(radians(point))))
            points.append((int(radius) + x1, y_offset + y1))
        pygame.draw.polygon(radio_bitmap, col1, points, 0)
        pygame.draw.polygon(radio_bitmap, col2, points, 1)
        x_size = int((radius * 2) + 4 + text_bitmap.get_rect().width + 1)
        button_complete = pygame.surface.Surface((x_size, text_height), pygame.SRCALPHA)
        button_complete.blit(radio_bitmap, (0, 0))
        button_complete.blit(text_bitmap, (int(radius * 2) + 4, 0))
        return button_complete

    def draw_button_graphic(self, text, rect):
        x, y, w, h = rect
        saved = []
        set_font('normal')
        text_bitmap = render_text(text)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        idle_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_box(idle_surface, 'idle', Rect(0, 0, w, h), colours)
        idle_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(idle_surface)
        text_bitmap = render_text(text)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        hover_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_box(hover_surface, 'hover', Rect(0, 0, w, h), colours)
        hover_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(hover_surface)
        text_bitmap = render_text(text, True)
        text_x = centre(w, text_bitmap.get_rect().width)
        text_y = centre(h, text_bitmap.get_rect().height)
        armed_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_box(armed_surface, 'armed', Rect(0, 0, w, h), colours)
        armed_surface.blit(text_bitmap, (text_x, text_y))
        saved.append(armed_surface)
        set_last_font()
        return saved

    def draw_box_graphic(self, rect):
        x, y, w, h = rect
        saved = []
        idle_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_box(idle_surface, 'idle', Rect(0, 0, w, h), colours)
        saved.append(idle_surface)
        hover_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_box(hover_surface, 'hover', Rect(0, 0, w, h), colours)
        saved.append(hover_surface)
        armed_surface = pygame.surface.Surface((w, h)).convert()
        self.draw_box(armed_surface, 'armed', Rect(0, 0, w, h), colours)
        saved.append(armed_surface)
        return saved

    def draw_box(self, surface, state, rect, colours):
        if state == 'idle':
            self.draw_box_frame(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['medium'], rect)
        elif state == 'hover':
            self.draw_box_frame(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['light'], rect)
        elif state == 'armed':
            self.draw_box_frame(surface, colours['none'], colours['light'], colours['none'], colours['full'], colours['dark'], rect)

    def draw_box_frame(self, surface, ul, lr, ul_d, lr_d, background, surface_rect):
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
