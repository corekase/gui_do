from enum import Enum
from ..constants import GType
from .widget import Widget
from ..bitmapfactory import BitmapFactory

FrState = Enum('State', ['Idle', 'Hover', 'Armed'])

class Frame(Widget):
    def __init__(self, gui, id, rect):
        super().__init__(id, rect)
        self.GType = GType.Frame
        self.factory = BitmapFactory()
        self.idle, self.hover, self.armed = self.factory.draw_frame_bitmaps(rect)
        self.state = FrState.Idle

    def handle_event(self, _, _a):
        return False

    def draw(self):
        super().draw()
        if self.state == FrState.Idle:
            self.surface.blit(self.idle, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == FrState.Hover:
            self.surface.blit(self.hover, (self.draw_rect.x, self.draw_rect.y))
        elif self.state == FrState.Armed:
            self.surface.blit(self.armed, (self.draw_rect.x, self.draw_rect.y))
