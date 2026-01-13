import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, Window, set_backdrop, set_font, set_cursor, restore_pristine
from gui import colours, centre, set_grid_properties, gridded
from gui import GKind, Canvas, CKind, Label, Button, GroupButton, Toggle, Scrollbar, Image

class Life:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        self.screen_rect = self.screen.get_rect()
        # set window caption
        pygame.display.set_caption('Conway\'s Game of Life')
        fonts = (('titlebar', 'Ubuntu-B.ttf', 14), ('normal', 'Gimbot.ttf', 16))
        self.gui = gui_init(self.screen, fonts)
        set_font('normal')
        set_backdrop('backdrop.jpg')
        widget_height = 28
        add(Button('exit', Rect(10, 1042, 70, widget_height), 1, 'Exit'))
        width, height = 500, 500
        pos = (centre(self.screen_rect.width, width), centre(self.screen_rect.height, height))
        self.life_win = Window('Conway\'s Game of Life', pos, (width, height))
        self.canvas = add(Canvas('life', Rect(10, 10, width - 20, height - 58), canvas_callback=self.handle_canvas, automatic_pristine=True))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_size()
        self.life = set()
        set_grid_properties((30, height - 38), 90, widget_height, 2)
        self.toggle_life = add(Toggle('run', gridded(0, 0), 2, False, 'Stop', 'Start'))
        add(Button('reset', gridded(1, 0), 1, 'Reset'), self.reset)
        set_cursor((1, 1), 'cursor.png')
        self.reset()
        self.dragging = False
        self.running = True

    def run(self):
        fps = 60
        clock = pygame.time.Clock()
        while self.running:
            restore_pristine()
            if not self.canvas.focused():
                self.dragging = False
            self.handle_events()
            if self.life_win.get_visible():
                if self.toggle_life.read():
                    self.generate()
                self.draw_life()
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

    def reset(self):
        self.origin_x, self.origin_y = self.canvas_rect.centerx, self.canvas_rect.centery
        self.cell_size = 6
        self.toggle_life.set(False)
        self.life = set({(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)})

    def generate(self):
        neighbours = ((-1, -1), (-1,  0), (-1, 1), (0, -1),
                      ( 0,  1), ( 1, -1), ( 1, 0), (1,  1))
        def population(cell):
            count = 0
            for position in neighbours:
                position_x = cell[0] + position[0]
                position_y = cell[1] + position[1]
                if (position_x, position_y) in self.life:
                    count += 1
            return count
        new_life = set()
        for cell in self.life:
            # Check this cell
            if population(cell) == 3 or \
               population(cell) == 2:
                   new_life.add(cell)
            for new_cell in neighbours:
                test_cell = (cell[0] + new_cell[0],
                             cell[1] + new_cell[1])
                if population(test_cell) == 3:
                   new_life.add(test_cell)
        self.life = new_life

    def draw_life(self):
        self.canvas_surface.set_clip(Rect(1, 1, self.canvas_rect.width - 2, self.canvas_rect.height - 2))
        for cell in self.life:
            size_x = size_y = self.cell_size
            xpos, ypos = cell
            xpos = self.origin_x + (xpos * self.cell_size)
            ypos = self.origin_y + (ypos * self.cell_size)
            bounded = (xpos >= -self.cell_size) and (xpos <= self.canvas_rect.width) and \
                      (ypos >= -self.cell_size) and (ypos <= self.canvas_rect.height)
            if bounded:
                if xpos < 0:
                    size_x = xpos + self.cell_size
                    xpos = 0
                if ypos < 0:
                    size_y = ypos + self.cell_size
                    ypos = 0
                self.canvas_surface.fill(colours['full'], Rect(xpos, ypos, size_x - 1, size_y - 1))
        self.canvas_surface.set_clip(None)

    def handle_canvas(self):
        CEvent = self.canvas.read_event()
        if CEvent != None:
            if CEvent.type == CKind.MouseButtonDown:
                if CEvent.button == 3:
                    self.dragging = True
            elif CEvent.type == CKind.MouseButtonUp:
                if CEvent.button == 3:
                    self.dragging = False
            elif CEvent.type == CKind.MouseMotion:
                if self.dragging:
                    x, y = CEvent.rel[0], CEvent.rel[1]
                    self.origin_x += x
                    self.origin_y += y
            elif CEvent.type == CKind.MouseWheel:
                if CEvent.y != None:
                    self.cell_size += (CEvent.y * 2)
                    if self.cell_size < 6:
                        self.cell_size = 6
                    elif self.cell_size > 24:
                        self.cell_size = 24

if __name__ == '__main__':
    Life().run()
