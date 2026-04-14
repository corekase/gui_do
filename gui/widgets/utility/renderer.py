import pygame
from pygame import Rect

class Renderer:
    def __init__(self, gui):
        self.gui = gui

    def draw(self):
        # draw all widgets to their surfaces
        if self.gui.buffered:
            self.gui.bitmaps.clear()
        for widget in self.gui.widgets:
            if widget.visible:
                # save the bitmap area under the widgets if buffered
                if self.gui.buffered:
                    self.gui.bitmaps.insert(0, (self.gui.copy_graphic_area(self.gui.surface, widget.get_rect()), widget.get_rect()))
                # draw the widget
                widget.draw()
        for window in self.gui.windows:
            if window.visible:
                # save the bitmap area under the window if buffered
                if self.gui.buffered:
                    self.gui.bitmaps.insert(0, (self.gui.copy_graphic_area(self.gui.surface, window.get_window_rect()), window.get_window_rect()))
                if window is self.gui.windows[-1]:
                    window.draw_title_bar_active()
                else:
                    window.draw_title_bar_inactive()
                window.draw_window()
                for widget in window.widgets:
                    # draw the widget
                    if widget.visible:
                        widget.draw()
                self.gui.surface.blit(window.surface, (window.x, window.y))
        # if locked mode is active always use the locked mode mouse position
        if self.gui.mouse_locked:
            self.gui.mouse_pos = self.gui.lock_area(self.gui.mouse_pos)
        # draw mouse cursor
        cursor_rect = Rect(self.gui.mouse_pos[0] - self.gui.cursor_hotspot[0], self.gui.mouse_pos[1] - self.gui.cursor_hotspot[1],
                           self.gui.cursor_rect.width, self.gui.cursor_rect.height)
        # save the bitmap area under the window if buffered
        if self.gui.buffered:
            self.gui.bitmaps.insert(0, (self.gui.copy_graphic_area(self.gui.surface, cursor_rect), cursor_rect))
        self.gui.surface.blit(self.gui.cursor_image, cursor_rect)

    def undraw(self):
        # reverse the bitmaps that were under each gui object drawn, if buffered is false then
        # the client does not call this method at all
        for bitmap, rect in self.gui.bitmaps:
            self.gui.surface.blit(bitmap, rect)
        self.gui.bitmaps.clear()
