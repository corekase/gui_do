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
        set_grid_properties((10, height - 38), 100, widget_height, 2)
        add(Button('scanlines', gridded(0, 0), 1, 'Scanlines'))
        add(Button('recursive1', gridded(1, 0), 1, 'Recurse 1'))
        set_cursor((1, 1), 'cursor.png')
        self.running = True
        self.recurse = False
        self.tasks = []

    def run(self):
        fps = 60
        clock = pygame.time.Clock()
        self.mandel_setup()
        while self.running:
            restore_pristine()
            self.cooperative_scheduler()
            self.handle_events()
            self.gui.draw_gui()
            pygame.display.flip()
            clock.tick(fps)
        pygame.quit()

    def handle_events(self):
        for event in self.gui.events():
            if event.type == GKind.Widget:
                if event.widget_id == 'scanlines':
                    self.canvas_surface.fill(colours['medium'])
                    self.add_task(self.mandel_scanlines)
                elif event.widget_id == 'recursive1':
                    self.canvas_surface.fill(colours['medium'])
                    self.mandel_recursive(self.canvas_rect)
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

    def cooperative_scheduler(self):
        if len(self.tasks) > 0:
            new_tasks = []     
            for task in self.tasks:
                try:
                    next(task)
                    new_tasks.append(task)
                except StopIteration:
                    pass
            self.tasks = new_tasks

    def add_task(self, task, params=None):
        t1 = task()
        self.tasks += [t1]
        if params != None:
            next(t1)
            t1.send(params)

    def mandel_recursive(self, area:Rect):
        x, y, r, b = area.x, area.y, area.right, area.bottom
        cenx, ceny = area.centerx, area.centery
        # fill if all same points
        tl = self.pixel(x, y)
        tr = self.pixel(r, y)
        bl = self.pixel(x, b)
        br = self.pixel(r, b)
        if tl == tr and bl == br and bl == tl:
            self.canvas_surface.fill(self.col(tl), area)
            return
        if area.width > 2 or area.height > 2:
            widx = cenx - x + 1
            widy = ceny - y + 1
            self.mandel_recursive(Rect(x, y, widx, widy))
            self.mandel_recursive(Rect(cenx, y, widx, widy))
            self.mandel_recursive(Rect(cenx, ceny, widx, widy))
            self.mandel_recursive(Rect(x, ceny, widx, widy))
        else:
            self.canvas_surface.set_at((x, y), self.col(tl))
            self.canvas_surface.set_at((x + 1, y), self.col(tr))
            self.canvas_surface.set_at((x, y + 1), self.col(bl))
            self.canvas_surface.set_at((x + 1, y + 1), self.col(br))
            return

    def mandel_scanlines(self):
        for y in range(self.mandel_height):
            for x in range(self.mandel_width):
                self.canvas_surface.set_at((x, y), self.col(self.pixel(x, y)))
            if (y % 4) == 0:
                yield

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

    def col(self, escape):
        cols = (Color(66, 30, 15), Color(25, 7, 26), Color(9, 1, 47), Color(4, 4, 73),
                Color(0, 7, 100), Color(12, 44, 138), Color(24, 82, 177), Color(57, 125, 209),
                Color(134, 181, 229), Color(211, 236, 248), Color(241, 233, 191), Color(248, 201, 95),
                Color(255, 170, 0), Color(204, 128, 0), Color(153, 87, 0), Color(106, 52, 3))
        if escape == (self.max_iter - 1):
            plot_col = Color(0, 0, 0)
        else:
            plot_col = cols[escape % 16]
        return plot_col

if __name__ == '__main__':
    Mandel().run()
