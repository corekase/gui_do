from pygame import Rect

# named colour values, in one location to change everywhere
colours = {'full': (255, 255, 255), 'light': (0, 200, 200), 'medium': (0, 150, 150), 'dark': (0, 100, 100), 'none': (0, 0, 0),
           'text': (255, 255, 255), 'highlight': (238, 230, 0), 'background': (0, 60, 60)}

# widget is the base class all gui widgets inherit from
class Widget:
    def __init__(self, id, rect):
        # gui for the widget
        self.gui = None
        # surface to draw the widget on
        self.surface = None
        # window widget may be attached to
        self.window = None
        # identifier for widget, can be any kind like int or string
        self.id = id
        # rect for widget position and size on the surface
        self.rect = Rect(rect)
        # callback function
        self.callback = None
        # before widget is first drawn, save what was there in this bitmap
        self.pristine = None
        # whether or not the widget is visible
        self.visible = True
        # callback of the widget
        self.callback = None
        # -> To-do:
        #    if a widget is potentially transparent, like image and label,
        #    then automatically handle, depending on this flag, the saving
        #    and restoring of the pristine surface with the widget surface
        #    because of incorrect screen output if you don't
        self.transparent = False

    def save_pristine(self):
        # update the pristine bitmap
        from ..command import copy_graphic_area
        self.pristine = copy_graphic_area(self.surface, self.rect).convert()

    def set_visible(self, visible):
        self.visible = visible

    def get_visible(self):
        return self.visible

    def get_collide(self, window=None):
        from ..command import convert_to_window
        collide = self.rect.collidepoint(convert_to_window(self.gui.get_mouse_pos(), window))
        if collide:
            if self.gui.last_widget != self.gui.current_widget:
                if self.gui.last_widget != None:
                    self.gui.last_widget.leave()
                    self.gui.last_widget = None
            self.gui.last_widget = self.gui.current_widget
            self.gui.current_widget = self
        return collide

    def handle_event(self, _, _a):
        # implement in subclasses
        pass

    def get_rect(self):
        # return the widget rect
        return Rect(self.rect)

    def draw(self):
        from ..command import restore_pristine
        # handle transparency
        if self.transparent:
            restore_pristine(self.rect, self.window)

    def leave(self):
        # what to do when a widget loses focus
        pass
