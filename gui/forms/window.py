import pygame
from pygame import Rect
from pygame.draw import rect
from ..guimanager import GuiManager
from ..utility import set_font, set_last_font, render_text, centre
from ..widgets.frame import Frame, State, colours

class Window:
    def __init__(self, name, title, pos, size):
        self.gui = GuiManager()
        # window x and y position from the main surface coordinate, not the titlebar
        self.x, self.y = pos
        self.width, self.height = size
        # titlebar size
        self.titlebar_size = 20
        # window surface
        self.surface = pygame.surface.Surface(size).convert()
        # widgets on that surface
        self.widgets = []
        # add this window to the gui
        self.gui.add_window(name, self)
        # make this object the destination for gui.add commands
        self.gui.set_active_object(self)
        # make a frame for the backdrop of the window surface
        frame = Frame('window_frame', Rect(0, 0, size[0], size[1]))
        frame.state = State.IDLE
        frame.surface = self.surface
        # and make that frame the first widget in the surface list
        # and it is not added to the gui manager, only the list
        self.widgets.insert(0, frame)
        # make a title bar graphic
        self.title_bar_graphic = self.make_title_bar_graphic(title)
        # and store the rect for it
        self.title_bar_rect = self.title_bar_graphic.get_rect()
        # set the window to the position passed in
        self.set_pos(pos)
        # whether a window is shown or hidden
        self.visible = True

    def make_title_bar_graphic(self, title):
        set_font('titlebar')
        text_bitmap = render_text(title)
        title_surface = pygame.surface.Surface((self.width, self.titlebar_size)).convert()
        frame = Frame('titlebar_frame', Rect(0, 0, self.width, self.titlebar_size))
        frame.state = State.ARMED
        frame.surface = title_surface
        frame.draw()
        title_surface.blit(text_bitmap, (4, centre(self.titlebar_size, 10) - 2))
        set_last_font()
        self.window_widget_raised = self.make_window_widget(colours['full'], colours['medium'])
        return title_surface

    def make_window_widget(self, col1, col2):
        surface = pygame.surface.Surface((self.titlebar_size, self.titlebar_size), pygame.SRCALPHA)
        rect(surface, col1, Rect(2, 2, 8, 8))
        rect(surface, colours['none'], Rect(2, 2, 8, 8), 1)
        rect(surface, col2, Rect(6, 6, 8, 8))
        rect(surface, colours['none'], Rect(6, 6, 8, 8), 1)
        return surface

    def draw_title_bar(self):
        self.gui.surface.blit(self.title_bar_graphic, (self.x, self.y - self.titlebar_size))
        self.gui.surface.blit(self.window_widget_raised, self.get_widget_rect())

    def get_rect(self):
        # total rect of the window including titlebar and surface
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.height + self.titlebar_size)

    def get_widget_rect(self):
        return Rect(self.x + self.width - self.titlebar_size + 2, self.y - self.titlebar_size + 2, self.titlebar_size, self.titlebar_size)

    def set_pos(self, pos):
        self.x, self.y = pos
        self.title_bar_rect = Rect(self.x, self.y - self.titlebar_size, self.width, self.titlebar_size)

    def get_name(self):
        # return the name of the window
        return self.name
