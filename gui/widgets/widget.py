from pygame import Rect

# named colour values, in one location to change everywhere
colours = {'full': (255, 255, 255), 'light': (0, 200, 200), 'medium': (0, 150, 150), 'dark': (0, 100, 100), 'none': (0, 0, 0),
           'text': (255, 255, 255), 'highlight': (238, 230, 0), 'background': (0, 60, 60)}

# widget is the base class all gui widgets inherit from
class Widget:
    def __init__(self, id, rect):
        # surface to draw the widget on
        self.surface = None
        # identifier for widget, can be any kind like int or string
        self.id = id
        # rect for widget position and size on the surface
        self.rect = Rect(rect)
        # callback function
        self.callback = None
        # whether a widget is shown or hidden
        self.visible = True
        # whether the widget is dirty for the gui manager, every widget starts dirty
        self.dirty = True
        # before widget is first drawn, save what was there in this bitmap
        self.pristine = None

    def save_pristine(self):
        # update the pristine bitmap
        from ..utility import copy_graphic_area
        self.pristine = copy_graphic_area(self.surface, self.rect).convert()

    def handle_event(self, _, _a):
        # implement in subclasses
        pass

    def get_rect(self):
        # return the widget rect
        return Rect(self.rect)

    def draw(self):
        # implement in subclasses
        pass

    def leave(self):
        # what to do when a widget loses focus
        pass
