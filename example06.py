import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, set_backdrop, load_font, set_font
from gui import add, set_cursor, centre, Window, colours
from gui import GKind, Label, Button, Canvas, CKind, ToggleButton

class Demo:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # set window caption
        pygame.display.set_caption('gui_do')
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        # create a gui manager
        self.gui = gui_init(self.screen)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # load fonts
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # main label
        set_font('gui_do')
        self.gui_do_label = add(Label((50, 50),'gui_do', automatic_pristine=True))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'), self.exit)
        width, height = 700, 700
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        Window('Conway\'s Game of Life', (window_x, window_y), (width, height))
        self.canvas = add(Canvas('life', Rect(10, 10, width - 20, height - 50), automatic_pristine=True))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_rect()
        x_base = self.canvas_rect.x
        y_base = self.canvas_rect.y
        self.origin_x = self.canvas_rect.centerx - x_base
        self.origin_y = self.canvas_rect.centery - y_base
        self.viewport_x = 0
        self.viewport_y = 0
        self.toggle = add(ToggleButton('run', Rect(10, height - 30, 120, 20), False, 'Stop', 'Start'))
        self.button = add(Button('reset', Rect(140, height - 30, 120, 20), 'Reset'))
        self.cell_size = 4
        self.life = set()
        self.reset()
        self.dragging = False
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # whether to draw the boxes
        while self.running:
            # handle events
            self.handle_events()
            # draw current cycle
            self.draw()
            # generate new cycle
            if self.toggle.read():
                self.generate()
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
            # undraw gui
            self.gui.undraw_gui()
        # release resources
        pygame.quit()

    def handle_events(self):
        # update internal gui timers
        self.gui.timers.update()
        # handle the pygame event queue
        if not self.canvas.focused():
            self.dragging = False
        for raw_event in pygame.event.get():
            # process event queue
            event = self.gui.handle_event(raw_event)
            if event.type == GKind.Pass:
                # no operation
                continue
            if event.type == GKind.Quit:
                # handle window close widget or alt-f4 keypress
                self.running = False
                return
            if event.type == GKind.Widget:
                if event.widget_id == 'reset':
                    self.toggle.pushed = False
                    self.reset()
                elif event.widget_id == 'life':
                    canvas_event = self.canvas.read_event()
                    if canvas_event.type == CKind.MouseButtonDown:
                        if canvas_event.button == 3:
                            self.dragging = True
                    elif canvas_event.type == CKind.MouseButtonUp:
                        if canvas_event.button == 3:
                            self.dragging = False
                    elif canvas_event.type == CKind.MouseMotion:
                        if self.dragging:
                            self.viewport_x += canvas_event.rel[0]
                            self.viewport_y += canvas_event.rel[1]
                    elif canvas_event.type == CKind.MouseWheel:
                        if canvas_event.y != None:
                            self.cell_size += (canvas_event.y * 2)
                            if self.cell_size < 3:
                                self.cell_size = 3
                            elif self.cell_size > 16:
                                self.cell_size = 16
            elif event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # handle escape key
                    self.running = False

    # callbacks
    def exit(self):
        self.running = False

    def reset(self):
        self.viewport_x = self.viewport_y = 0
        self.cell_size = 4
        # the starting configuration of the Life grid
        self.life = set({(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)})

    def generate(self):
        # Coordinates around a cell, given as a delta table
        neighbours = ((-1, -1), (-1,  0), (-1, 1), (0, -1),
                      (0,   1), ( 1, -1), ( 1, 0), (1,  1))
        def population(cell):
            count = 0
            # For the delta table entries generate tuples of (x, y) and
            # then test them for membership in the life set
            for position in neighbours:
                position_x = cell[0] + position[0]
                position_y = cell[1] + position[1]
                if (position_x, position_y) in self.life:
                    count += 1
            return count
        # For every cell in the life set check the cell and its
        # neighbours for the population conditions
        new_life = set()
        for cell in self.life:
            # Check this cell
            if population(cell) == 3 or \
               population(cell) == 2:
                   new_life.add(cell)
            # Check all the neighbours of this cell
            for new_cell in neighbours:
                test_cell = (cell[0] + new_cell[0],
                             cell[1] + new_cell[1])
                if population(test_cell) == 3:
                   new_life.add(test_cell)
        # Replace the old set with the new
        self.life = new_life

    def draw(self):
        # Draw contents of map onto display
        for cell in self.life:
            # Unpack x and y cell coordinates
            xpos, ypos = cell
            xpos = self.origin_x + self.viewport_x + (xpos * self.cell_size)
            ypos = self.origin_y + self.viewport_y + (ypos * self.cell_size)
            # Check to see if the cell is on screen and if so draw it
            bounded = (xpos >= 0) and (xpos <= self.canvas_rect.width) and \
                      (ypos >= 0) and (ypos <= self.canvas_rect.height)
            if bounded:
                self.canvas_surface.fill(colours['full'], Rect(xpos, ypos, self.cell_size - 1, self.cell_size - 1))

if __name__ == '__main__':
    Demo().run()
