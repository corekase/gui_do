from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from ..guimanager import GuiManager
from ..utility import render_text, centre, convert_to_window
from .frame import Frame, FrameState

class Button(Frame):
    def __init__(self, id, rect, text):
        # initialize common widget values
        super().__init__(id, rect)
        self.gui = GuiManager()
        # button state
        self.state = FrameState.IDLE
        # text bitmaps
        self.text_bitmap = render_text(text)
        self.text_highlight_bitmap = render_text(text, True)
        # get centred dimensions for both x and y ranges
        text_x = self.rect.x + centre(self.rect.width, self.text_bitmap.get_rect().width) - 1
        text_y = self.rect.y + centre(self.rect.height, self.text_bitmap.get_rect().height) - 1
        # store the position for later blitting
        self.position = text_x, text_y

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
        # draw the button frame
        super().draw()
        # draw the button text
        if self.state == FrameState.ARMED:
            bitmap = self.text_highlight_bitmap
        else:
            bitmap = self.text_bitmap
        self.surface.blit(bitmap, self.position)
