from .frame import Frame, State
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from .utility import render_text, centre, screen_to_window

class Button(Frame):
    def __init__(self, id, rect, text):
        # initialize common widget values
        super().__init__(id, rect)
        # button state
        self.state = State.IDLE
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
        if window != None:
            pos = screen_to_window(event.pos, window)
            collision = self.rect.collidepoint(pos)
        else:
            collision = self.rect.collidepoint(event.pos)
        # manage the state of the button
        if (self.state == State.IDLE) and collision:
            self.state = State.HOVER
        if self.state == State.HOVER:
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.IDLE
            if (event.type == MOUSEBUTTONDOWN) and collision:
                if event.button == 1:
                    self.state = State.ARMED
        if self.state == State.ARMED:
            if (event.type == MOUSEBUTTONUP) and collision:
                if event.button == 1:
                    # button clicked
                    self.state = State.HOVER
                    return True
            if (event.type == MOUSEMOTION) and (not collision):
                self.state = State.IDLE
        # button not clicked
        return False

    def draw(self):
        # draw the button frame
        super().draw()
        # draw the button text
        if self.state == State.ARMED:
            bitmap = self.text_highlight_bitmap
        else:
            bitmap = self.text_bitmap
        self.surface.blit(bitmap, self.position)
