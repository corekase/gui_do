from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..guimanager import GuiManager
from ..utility import convert_to_window
from .frame import Frame, FrameState
from ..graphicfactory import GraphicFactory

class Button(Frame):
    def __init__(self, id, rect, text):
        # initialize common widget values
        super().__init__(id, rect)
        self.gui = GuiManager()
        factory = GraphicFactory()
        self.idle, self.hover, self.armed = factory.draw_button_bitmap(text, rect)
        self.state = FrameState.IDLE
        self.add_dirty()

    def handle_event(self, event, window):
        if event.type not in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            # no matching events for button logic
            return False
        # is the mouse position within the button rect
        collision = self.rect.collidepoint(convert_to_window(self.gui.lock_area(event.pos), window))
        # manage the state of the button
        if (self.state == FrameState.IDLE) and collision:
            self.state = FrameState.HOVER
        if self.state == FrameState.HOVER:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = FrameState.IDLE
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    self.state = FrameState.ARMED
        if self.state == FrameState.ARMED:
            if (event.type == MOUSEBUTTONUP) and collision:
                if event.button == 1:
                    # button clicked
                    self.state = FrameState.IDLE
                    return True
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = FrameState.IDLE
        # button not clicked
        return False

    def leave(self):
        self.state = FrameState.IDLE

    def draw(self):
        if self.state == FrameState.IDLE:
            self.surface.blit(self.idle, (self.rect.x, self.rect.y))
        elif self.state == FrameState.HOVER:
            self.surface.blit(self.hover, (self.rect.x, self.rect.y))
        elif self.state == FrameState.ARMED:
            self.surface.blit(self.armed, (self.rect.x, self.rect.y))
