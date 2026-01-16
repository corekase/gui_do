import pygame
from pygame import Rect, Color, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, Window, set_backdrop, set_font, set_cursor, restore_pristine
from gui import centre, set_grid_properties, gridded
from gui import GKind, Button, Canvas, Scheduler
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
        width, height = 650, 650
        pos = (centre(self.screen_rect.width, width), centre(self.screen_rect.height, height))
        self.mandel_win = Window('Mandelbrot', pos, (width, height))
        self.canvas = add(Canvas('mandel', Rect(10, 10, width - 20, height - (widget_height * 2)), canvas_callback=self.handle_canvas))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_surface.fill(colours['medium'])
        self.canvas_rect = self.canvas.get_size()
        set_grid_properties((10, height - widget_height - 10), 100, widget_height, 2)
        add(Button('clear', gridded(0, 0), 1, 'Clear'))
        add(Button('iterative', gridded(1, 0), 1, 'Iterative'))
        add(Button('recursive', gridded(2, 0), 1, 'Recursive'))
        set_cursor((1, 1), 'cursor.png')
        self.running = True
        self.schedules = Scheduler()

    def run(self):
        fps = 60
        clock = pygame.time.Clock()
        self.mandel_setup()
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
                if event.widget_id == 'exit':
                    self.running = False
                elif event.widget_id == 'clear':
                    self.schedules.remove_task('iter')
                    self.schedules.remove_task('recu')
                    self.canvas_surface.fill(colours['medium'])
                elif not self.schedules.task_match('iter', 'recu'):
                    if event.widget_id == 'iterative':
                        self.canvas_surface.fill(colours['medium'])
                        self.schedules.add_task('iter', 0.017, self.mandel_iterative)
                    elif event.widget_id == 'recursive':
                        self.canvas_surface.fill(colours['medium'])
                        self.schedules.add_task('recu', 0.017, self.mandel_recursive, self.canvas_rect)
            elif event.type == GKind.KeyDown:
                if event.key == K_ESCAPE:
                    self.running = False
            elif event.type == GKind.Quit:
                self.running = False

    def handle_canvas(self):
        _ = self.canvas.read_event()

    def mandel_iterative(self, id, _):
        for y in range(self.mandel_height):
            for x in range(self.mandel_width):
                self.canvas_surface.set_at((x, y), self.col(self.pixel(x, y)))
            if self.schedules.poll_task_time(id):
                yield

    def mandel_recursive(self, id, area):
        if self.schedules.poll_task_time(id):
            yield
        x, y, w, h = area
        top_left = self.pixel(x, y)
        accuracy = 2
        not_hit = True
        for x_test in range(0, w, accuracy):
            if (self.pixel(x + x_test, y) != top_left) or (self.pixel(x + x_test, y + h - 1) != top_left):
                not_hit = False
                break
        if not_hit:
            for y_test in range(0, h, accuracy):
                if (self.pixel(x, y + y_test) != top_left) or (self.pixel(x + w - 1, y + y_test) != top_left):
                    not_hit = False
                    break
        if not_hit:
            self.canvas_surface.fill(self.col(top_left), area)
            return
        if w > 2 or h > 2:
            half_x = (w + (w % 2)) // 2
            half_y = (h + (h % 2)) // 2
            yield from self.mandel_recursive(id, Rect(x, y, half_x, half_y))
            yield from self.mandel_recursive(id, Rect(x + half_x, y, half_x, half_y))
            yield from self.mandel_recursive(id, Rect(x + half_x, y + half_y, half_x, half_y))
            yield from self.mandel_recursive(id, Rect(x, y + half_y, half_x, half_y))
            return
        else:
            r, b = area.right - 1, area.bottom - 1
            top_right, bottom_left, bottom_right = self.pixel(r, y), self.pixel(x, b), self.pixel(r, b)
            self.canvas_surface.lock()
            self.canvas_surface.set_at((x, y), self.col(top_left))
            self.canvas_surface.set_at((x + 1, y), self.col(top_right))
            self.canvas_surface.set_at((x, y + 1), self.col(bottom_left))
            self.canvas_surface.set_at((x + 1, y + 1), self.col(bottom_right))
            self.canvas_surface.unlock()
            return

    def mandel_setup(self):
        self.max_iter = 96
        _, _, self.mandel_width, self.mandel_height = self.canvas_rect
        self.center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        self.scale = max((extent / self.mandel_width).real, (extent / self.mandel_height).imag)

    def pixel(self, x, y):
        c = self.center + (x - self.mandel_width // 2 + (y - self.mandel_height // 2) * 1j) * self.scale
        z = 0
        for k in range(self.max_iter):
            z = z ** 2 + c
            if (z * z.conjugate()).real > 4.0:
                break
        return k

    def col(self, k):
        cols = (Color(66, 30, 15), Color(25, 7, 26), Color(9, 1, 47), Color(4, 4, 73),
                Color(0, 7, 100), Color(12, 44, 138), Color(24, 82, 177), Color(57, 125, 209),
                Color(134, 181, 229), Color(211, 236, 248), Color(241, 233, 191), Color(248, 201, 95),
                Color(255, 170, 0), Color(204, 128, 0), Color(153, 87, 0), Color(106, 52, 3))
        if k == (self.max_iter - 1):
            screen_colour = Color(0, 0, 0)
        else:
            screen_colour = cols[k % 16]
        return screen_colour

if __name__ == '__main__':
    Mandel().run()
