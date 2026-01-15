import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, Window, set_backdrop, set_font, set_cursor, restore_pristine
from gui import centre, set_grid_properties, gridded
from gui import GKind, Canvas, CKind, Label, Button, ButtonGroup, Toggle, Scrollbar, Image

class Mandel:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        self.screen_rect = self.screen.get_rect()
        # set window caption
        pygame.display.set_caption('Mandelbrot')
        fonts = (('titlebar', 'Ubuntu-B.ttf', 14), ('normal', 'Gimbot.ttf', 16))
        self.gui = gui_init(self.screen, fonts)
        set_font('normal')
        set_backdrop('backdrop.jpg')
        widget_height = 30
        add(Button('exit', Rect(10, 1042, 70, widget_height), 1, 'Exit'))
        width, height = 500, 500
        pos = (centre(self.screen_rect.width, width), centre(self.screen_rect.height, height))
        self.mandel_win = Window('Mandelbrot', pos, (width, height))
        self.canvas = add(Canvas('mandel', Rect(10, 10, width - 20, height - 58), canvas_callback=self.handle_canvas, automatic_pristine=True))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_size()
        set_grid_properties((30, height - 38), 90, widget_height, 2)
        self.run_toggle = add(Toggle('run', gridded(0, 0), 3, False, 'Stop', 'Start'))
        add(Button('reset', gridded(1, 0), 1, 'Reset'))
        set_cursor((1, 1), 'cursor.png')
        self.running = True

    def run(self):
        fps = 60
        clock = pygame.time.Clock()
        while self.running:
            restore_pristine()
            self.handle_events()
            if self.mandel_win.get_visible():
                if self.run_toggle.read():
                    pass
            self.gui.draw_gui()
            pygame.display.flip()
            clock.tick(fps)
        pygame.quit()

    def handle_events(self):
        for event in self.gui.events():
            if event.type == GKind.Widget:
                if event.widget_id == 'exit':
                    self.running = False
            elif event.type == GKind.KeyDown:
                if event.key == K_ESCAPE:
                    self.running = False
            elif event.type == GKind.Quit:
                self.running = False

    def handle_canvas(self):
        CEvent = self.canvas.read_event()
        if CEvent != None:
            pass

if __name__ == '__main__':
    Mandel().run()
