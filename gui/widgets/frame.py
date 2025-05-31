from enum import Enum
from .widget import Widget
from ..bitmapfactory import BitmapFactory

FrameState = Enum('FrameState', ['IDLE', 'HOVER', 'ARMED'])

class Frame(Widget):
    def __init__(self, id, rect):
        super().__init__(id, rect)
        self.factory = BitmapFactory()
        self.idle, self.hover, self.armed = self.factory.draw_frame_bitmaps(rect)
        self.state = FrameState.IDLE

    def handle_event(self, _, _a):
        return False

    def draw(self):
        # determine which colours to use depending on State
        if self.state == FrameState.IDLE:
            self.surface.blit(self.idle, (self.rect.x, self.rect.y))
        elif self.state == FrameState.HOVER:
            self.surface.blit(self.hover, (self.rect.x, self.rect.y))
        elif self.state == FrameState.ARMED:
            self.surface.blit(self.armed, (self.rect.x, self.rect.y))
