import pygame
from pygame import Rect
from ..guimanager import GuiManager
from ..bitmapfactory import BitmapFactory
from ..command import copy_graphic_area, set_active_object, set_backdrop, restore_pristine, colours
from ..widgets.frame import Frame, FrState

class WindowBase:
    def __init__(self, title, pos, size, backdrop=None):
        # windows don't need names because eventually they are going to be in banks which will be named
        self.gui = GuiManager()
        factory = BitmapFactory()
        # window x and y position from the main surface coordinate, not the titlebar
        self.x, self.y = pos
        self.width, self.height = size
        # titlebar size
        self.titlebar_size = 24
        # window surface
        self.surface = pygame.surface.Surface(size).convert()
        self.pristine = None
        if backdrop == None:
            # make a frame for the backdrop of the window surface
            frame = Frame('window_frame', Rect(0, 0, size[0], size[1]))
            frame.state = FrState.Idle
            frame.surface = self.surface
            frame.draw()
        else:
            set_backdrop(backdrop, self)
        self.window_save_pristine()
        # widgets on that surface
        self.widgets = []
        # set the window to the position passed in
        self.set_pos(pos)
        self.title_bar_inactive_bitmap, self.title_bar_active_bitmap = factory.draw_window_title_bar_bitmaps(title, self.width, self.titlebar_size)
        self.title_bar_rect = self.title_bar_active_bitmap.get_rect()
        self.window_widget_lower_bitmap = factory.draw_window_lower_widget_bitmap(self.titlebar_size, colours['full'], colours['medium'])
        # whether or not the window is visible
        self.visible = True

    def window_save_pristine(self):
        # update the window pristine bitmap
        # the window pristine bitmap can be used to undo widget bitmap damage to the contents
        self.pristine = copy_graphic_area(self.surface, self.surface.get_rect()).convert()

    def draw_title_bar_inactive(self):
        self.gui.surface.blit(self.title_bar_inactive_bitmap, (self.x, self.y - self.titlebar_size))
        lower_widget = self.get_widget_rect()
        lower_widget.y += 3
        self.gui.surface.blit(self.window_widget_lower_bitmap, lower_widget)

    def draw_title_bar_active(self):
        self.gui.surface.blit(self.title_bar_active_bitmap, (self.x, self.y - self.titlebar_size))
        lower_widget = self.get_widget_rect()
        lower_widget.y += 3
        self.gui.surface.blit(self.window_widget_lower_bitmap, lower_widget)

    def draw_window(self):
        # called when the gui manager is entering a window to process its widgets
        restore_pristine(self.surface.get_rect(), self)

    def get_title_bar_rect(self):
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.titlebar_size)

    def get_window_rect(self):
        # total rect of the window including titlebar and surface
        return Rect(self.x, self.y - self.titlebar_size, self.width, self.height + self.titlebar_size)

    def get_widget_rect(self):
        x, y, w, h = self.window_widget_lower_bitmap.get_rect()
        return Rect(self.x + self.width - self.titlebar_size + 1, self.y - self.titlebar_size + 1, w, h)

    def set_visible(self, visible):
        self.visible = visible

    def get_visible(self):
        return self.visible

    def set_pos(self, pos):
        self.x, self.y = pos
