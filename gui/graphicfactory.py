import pygame
from pygame import Rect
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
from pygame.draw import rect, line

class GraphicFactory:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080))
        self.running = True

        self.colours = {'full': (255, 255, 255), 'light': (0, 200, 200), 'medium': (0, 150, 150), 'dark': (0, 100, 100), 'none': (0, 0, 0),
                        'text': (255, 255, 255), 'highlight': (238, 230, 0), 'background': (0, 60, 60)}

        self.button_rect = Rect(0, 0, 60, 20)

        self.buttons = self.draw_button_graphics(self.button_rect)

    def run(self):
        fps = 60
        clock = pygame.time.Clock()
        bx, by = 10, 10
        while self.running:
            self.screen.fill(self.colours['background'])
            counter = 0
            for button in self.buttons.keys():
                x, y, w, h = self.button_rect
                self.screen.blit(self.buttons[button], Rect(bx + (w * counter) + (counter * 4), by, w, h))
                counter += 1
            self.handle_events()
            clock.tick(fps)
            pygame.display.flip()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False

    def draw_button_graphics(self, rect):
        x, y, w, h = rect
        saved = {}
        for state in 'idle', 'hover', 'armed':
            surface = pygame.surface.Surface((w, h)).convert()
            self.draw_box(surface, state, Rect(0, 0, w, h), self.colours)
            saved[state] = surface
        return saved

    def draw_box(self, surface, state, rect, colours):
        # determine which colours to use depending on State
        if state == 'idle':
            self.draw_box_frame(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['medium'], rect)
        elif state == 'hover':
            self.draw_box_frame(surface, colours['light'], colours['dark'], colours['full'], colours['none'], colours['light'], rect)
        elif state == 'armed':
            self.draw_box_frame(surface, colours['none'], colours['light'], colours['none'], colours['full'], colours['dark'], rect)

    def draw_box_frame(self, surface, ul, lr, ul_d, lr_d, background, surface_rect):
        # ul, lr = upper and left, lower and right lines
        # ul_d, lr_d = upper-left dot, lower-right dot
        # get positions and sizes
        x, y, width, height = surface_rect
        # lock surface for drawing
        surface.lock()
        # draw background
        rect(surface, background, surface_rect, 0)
        # draw frame upper and left lines
        line(surface, ul, (x, y), (x + width - 1, y))
        line(surface, ul, (x, y), (x, y + height - 1))
        # draw frame lower and right lines
        line(surface, lr, (x, y + height - 1), (x + width - 1, y + height - 1))
        line(surface, lr, (x + width - 1, y - 1), (x + width - 1, y + height - 1))
        # plot upper left dot
        surface.set_at((x + 1, y + 1), ul_d)
        # plot lower right dot
        surface.set_at((x + width - 2, y + height - 2), lr_d)
        # unlock surface
        surface.unlock()

if __name__ == '__main__':
    GraphicFactory().run()
