from pygame import Rect
from ...values.constants import CType
# widget is the base class all gui widgets inherit from

class Widget:
    def __init__(self, gui, id, rect):
        # gui reference
        self.gui = gui
        # widget type
        self.GType = None
        # form type
        self.ctype = CType.Widget
        # surface to draw the widget on
        self.surface = None
        # window widget may be attached to
        self.window = None
        # identifier for widget, can be any kind like int or string
        self.id = id
        # rect for widget drawing position and size on the surface
        self.draw_rect = Rect(rect)
        # rect for mouse collision
        self.hit_rect = None
        # before widget is first drawn, save what was there in this bitmap
        self.pristine = None
        # whether or not the widget is visible
        self.visible = True
        # callback of the widget
        self.callback = None
        # if this is true then if the widget calls the superclass draw defined in this
        # class then this class will restore the pristine image, return, and subclasses
        # continue drawing
        self.auto_restore_pristine = False

    def set_visible(self, visible):
        self.visible = visible

    def get_visible(self):
        return self.visible

    def get_collide(self, window=None):
        # Purely read-only collision check
        if self.hit_rect is None:
            return self.draw_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), window))
        return self.hit_rect.collidepoint(self.gui.convert_to_window(self.gui.get_mouse_pos(), window))

    def handle_event(self, _, _a):
        # implement in subclasses
        pass

    def get_rect(self):
        # rect that the guimanager uses for buffering
        return Rect(self.draw_rect)

    def get_size(self):
        # remove the x and y offset for where the widget is being drawn on a surface
        # and return just the rect dimensions
        _, _, w, h = self.draw_rect
        return Rect(0, 0, w, h)

    def draw(self):
        # if auto restore flag then restore the pristine bitmap
        if self.auto_restore_pristine:
            self.gui.restore_pristine(self.draw_rect, self.window)

    def leave(self):
        # what to do when a widget loses focus
        pass
