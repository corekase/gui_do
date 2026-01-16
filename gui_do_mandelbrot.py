import pygame
from pygame import Rect, Color, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, Window, set_backdrop, set_font, set_cursor, restore_pristine
from gui import centre, set_grid_properties, gridded
from gui import GKind, Canvas, CKind, Label, Button, ButtonGroup, Toggle, Scrollbar, Image
from gui import colours

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
        self.canvas = add(Canvas('mandel', Rect(10, 10, width - 20, height - 58), canvas_callback=self.handle_canvas))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_surface.fill(colours['medium'])
        self.canvas_rect = self.canvas.get_size()
        set_grid_properties((10, height - 38), 90, widget_height, 2)
        add(Button('generate', gridded(0, 0), 1, 'Generate'))
        set_cursor((1, 1), 'cursor.png')
        self.running = True

    def run(self):
        fps = 60
        clock = pygame.time.Clock()
        while self.running:
            restore_pristine()
            self.handle_events()
            self.gui.draw_gui()
            pygame.display.flip()
            clock.tick(fps)
        pygame.quit()

    def handle_events(self):
        for event in self.gui.events():
            if event.type == GKind.Widget:
                if event.widget_id == 'generate':
                    self.mandel()
                elif event.widget_id == 'exit':
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

    def mandel(self):
        cols = (Color(66, 30, 15), Color(25, 7, 26), Color(9, 1, 47), Color(4, 4, 73),
                Color(0, 7, 100), Color(12, 44, 138), Color(24, 82, 177), Color(57, 125, 209),
                Color(134, 181, 229), Color(211, 236, 248), Color(241, 233, 191), Color(248, 201, 95),
                Color(255, 170, 0), Color(204, 128, 0), Color(153, 87, 0), Color(0, 0, 0))
        def col(k):
            return cols[k % 16]
        # must be a multiple of 16 to line up with black colour on the palette
        max_iter = 128
        _, _, width, height = self.canvas_rect
        center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        scale = max((extent / width).real, (extent / height).imag)
        for j in range(height):
            for i in range(width):
                c = center + (i - width // 2 + (j - height // 2) * 1j) * scale
                z = 0
                for k in range(max_iter):
                    z = z**2 + c
                    if (z * z.conjugate()).real > 4.0:
                        break
                self.canvas_surface.set_at((i, j), col(k))

if __name__ == '__main__':
    Mandel().run()
