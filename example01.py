import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, Window, set_backdrop, set_font, set_cursor, restore_pristine
from gui import colours, centre, set_grid_properties, gridded
from gui import GKind, Canvas, CKind, Label, Button, PushButtonGroup, ToggleButton, Scrollbar, Image

class Demo:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # screen rect
        self.screen_rect = self.screen.get_rect()
        # set window caption
        pygame.display.set_caption('Demo')
        # create a gui manager
        fonts = [['titlebar', 'Wiltype.ttf', 16],
                 ['normal', 'Ubuntu-M.ttf', 16],
                 ['scroll', 'Gimbot.ttf', 32],
                 ['gui_do', 'Gimbot.ttf', 72]]
        self.gui = gui_init(self.screen, fonts)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # screen label
        set_font('gui_do')
        add(Label((50, 30), 'gui_do', True))
        set_font('normal')
        widget_height = 28
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1040, 70, widget_height), 'Exit'))
        # setup for the togglebuttons
        set_grid_properties((85, 1040), 120, widget_height, 4)
        # control whether the background circles are drawn
        self.circles_toggle = add(ToggleButton('circles', gridded(0, 0), True, 'Circles'))
        # control whether the pushboxes window is visible
        self.push_box_toggle = add(ToggleButton('push_window', gridded(1, 0), True, 'Pushboxes'))
        # control whether the pushradios window is visible
        self.push_radio_toggle = add(ToggleButton('push_radio', gridded(2, 0), True, 'Pushradios'))
        # control whether the life window is visible
        self.push_life_toggle = add(ToggleButton('push_life', gridded(3, 0), True, 'Life'))
        # control whether the scrollbar window is visible
        self.push_scrollbars_toggle = add(ToggleButton('push_scroll', gridded(4, 0), True, 'Scrollbars'))
        # make the pushboxes window
        self.pb_win = Window('Pushboxes', (50, 150), (140, 150))
        set_grid_properties((10, 10), 120, widget_height, 2)
        add(PushButtonGroup('pb1', gridded(0, 0), 'Pushbox', 'pb1', 0))
        add(PushButtonGroup('pb2', gridded(0, 1), 'Pushbox', 'pb1', 0))
        add(PushButtonGroup('pb3', gridded(0, 2), 'Pushbox', 'pb1', 0))
        add(Button('b1', gridded(0, 3), 'Button'))
        # make the pushradios window
        self.pr_win = Window('Pushradios', (50, 330), (140, 150))
        set_grid_properties((10, 10), 120, widget_height, 2)
        add(PushButtonGroup('pb4', gridded(0, 0), 'Pushradio', 'pb2', 1))
        add(PushButtonGroup('pb5', gridded(0, 1), 'Pushradio', 'pb2', 1))
        add(PushButtonGroup('pb6', gridded(0, 2), 'Pushradio', 'pb2', 1))
        add(Button('b2', gridded(0, 3), 'Button'))
        # make the Conway's Game of Life window
        width, height = 500, 500
        self.life_win = Window('Conway\'s Game of Life', (50, 510), (width, height))
        self.canvas = add(Canvas('life', Rect(10, 10, width - 20, height - 60), canvas_callback=self.handle_canvas, automatic_pristine=True))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_size()
        # a set to hold cell coordinates as tuples of x and y
        self.life = set()
        # toggle whether or not the simulation is processing
        self.toggle_life = add(ToggleButton('run', Rect(10, height - 40, 120, widget_height), False, 'Stop', 'Start'))
        # resets the simulation to a default state, uses a callback function
        add(Button('reset', Rect(140, height - 40, 120, widget_height), 'Reset'), self.reset)
        # make the scrollbar window
        width, height = 320, 362
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        self.sb_win = Window('Scrollbar Styles', (window_x, window_y), (width, height))
        # add scrollbar widgets to the window
        x = y = 10
        add(Scrollbar(f'scrollbar_a', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 0))
        y += 22
        add(Scrollbar(f'scrollbar_b', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 1))
        y += 22
        add(Scrollbar(f'scrollbar_c', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 2))
        y += 22
        add(Scrollbar(f'scrollbar_d', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 3))
        y += 24
        add(Scrollbar(f'scrollbar_e', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 0))
        x += 22
        add(Scrollbar(f'scrollbar_f', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 1))
        x += 22
        add(Scrollbar(f'scrollbar_g', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 2))
        x += 22
        add(Scrollbar(f'scrollbar_h', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 3))
        add(Image('realize', Rect(x + 25, y, 210, 210), 'realize.png', False))
        set_font('scroll')
        add(Label((x + 30, y + 215), 'Scrollbars!', True))
        set_font('normal')
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # reset the state of the simulation
        self.reset()
        # whether or not dragging with the right-mouse button over the canvas is active
        self.dragging = False
        # number of circles
        circles = 64
        # size of circles
        self.size = 12
        # circle positions
        self.positions = []
        # make bitmaps for circles
        from gui.bitmapfactory import BitmapFactory
        factory = BitmapFactory()
        circle_bitmap_a = factory.draw_radio_bitmap(self.size, colours['light'], colours['none'])
        circle_bitmap_b = factory.draw_radio_bitmap(self.size, colours['full'], colours['none'])
        # make position list for circles
        for _ in range(circles):
            x = randrange(self.size, self.screen_rect.width - (self.size * 2))
            y = randrange(self.size, self.screen_rect.height - (self.size * 2))
            dx = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            dy = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            self.positions.append((x, y, dx, dy, choice([circle_bitmap_a, circle_bitmap_b])))
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        while self.running:
            # restore the pristine area to the screen before drawing
            restore_pristine()
            # if the mouse isn't over the canvas then end the dragging state
            if not self.canvas.focused():
                self.dragging = False
            # draw the circles if their toggle is pushed
            if self.circles_toggle.read():
                self.update_circles(self.size)
            # update the visible windows
            self.pb_win.set_visible(self.push_box_toggle.read())
            self.pr_win.set_visible(self.push_radio_toggle.read())
            self.life_win.set_visible(self.push_life_toggle.read())
            self.sb_win.set_visible(self.push_scrollbars_toggle.read())
            # handle events
            self.handle_events()
            # if the life window is visible then handle it
            if self.life_win.get_visible():
                # generate a new cycle if the togglebutton is pressed
                if self.toggle_life.read():
                    self.generate()
                # draw life cells on the canvas
                self.draw_life()
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
        # release resources
        pygame.quit()

    def handle_events(self):
        # handle the gui event queue
        for event in self.gui.events():
            if event.type == GKind.Widget:
                if event.widget_id == 'exit':
                    # exit button was clicked
                    self.running = False
            elif event.type == GKind.KeyDown:
                if event.key == K_ESCAPE:
                    # escape key pressed
                    self.running = False
            elif event.type == GKind.Quit:
                # window close widget or alt-f4 keypress
                self.running = False

    # update the position and draw a bitmap at the position
    def update_circles(self, size):
        new_positions = []
        for x, y, dx, dy, bitmap in self.positions:
            x += dx
            y += dy
            if x < size or x > self.screen_rect.width - size:
                dx = -dx
            if y < size or y > self.screen_rect.height - size:
                dy = -dy
            self.screen.blit(bitmap, (x, y))
            new_positions.append((x, y, dx, dy, bitmap))
        self.positions = new_positions

    # reset the life simulation to a default state
    def reset(self):
        self.origin_x, self.origin_y = self.canvas_rect.centerx, self.canvas_rect.centery
        self.cell_size = 6
        self.toggle_life.set(False)
        # the starting configuration of the Life grid
        self.life = set({(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)})

    # function to generate a cycle of life
    def generate(self):
        # Coordinates around a cell, given as a delta table
        neighbours = ((-1, -1), (-1,  0), (-1, 1), (0, -1),
                      ( 0,  1), ( 1, -1), ( 1, 0), (1,  1))
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

    def draw_life(self):
        # Draw contents of the life cells onto the canvas surface
        self.canvas_surface.set_clip(Rect(1, 1, self.canvas_rect.width - 2, self.canvas_rect.height - 2))
        for cell in self.life:
            # set initial cell sizes
            size_x = size_y = self.cell_size
            # Unpack x and y cell coordinates
            xpos, ypos = cell
            # calculate the graphical coordinate of the cell
            xpos = self.origin_x + (xpos * self.cell_size)
            ypos = self.origin_y + (ypos * self.cell_size)
            # Check to see if the cell is on screen and if so draw it
            bounded = (xpos >= -self.cell_size) and (xpos <= self.canvas_rect.width) and \
                      (ypos >= -self.cell_size) and (ypos <= self.canvas_rect.height)
            if bounded:
                # if either xpos or ypos are less than zero trim the cell drawing size
                if xpos < 0:
                    size_x = xpos + self.cell_size
                    xpos = 0
                if ypos < 0:
                    size_y = ypos + self.cell_size
                    ypos = 0
                self.canvas_surface.fill(colours['full'], Rect(xpos, ypos, size_x - 1, size_y - 1))
        self.canvas_surface.set_clip(None)

    # canvas callback function
    def handle_canvas(self):
        # read the event from the canvas widget
        CEvent = self.canvas.read_event()
        if CEvent != None:
            # parse that event by kind and parameters
            if CEvent.type == CKind.MouseButtonDown:
                # right-mouse button pressed, enter dragging state
                if CEvent.button == 3:
                    self.dragging = True
            elif CEvent.type == CKind.MouseButtonUp:
                # right-mouse button released, exit dragging state
                if CEvent.button == 3:
                    self.dragging = False
            elif CEvent.type == CKind.MouseMotion:
                # if dragging then track relative position
                if self.dragging:
                    x, y = CEvent.rel[0], CEvent.rel[1]
                    self.origin_x += x
                    self.origin_y += y
            elif CEvent.type == CKind.MouseWheel:
                # handle the mouse wheel
                if CEvent.y != None:
                    self.cell_size += (CEvent.y * 2)
                    if self.cell_size < 6:
                        self.cell_size = 6
                    elif self.cell_size > 24:
                        self.cell_size = 24

if __name__ == '__main__':
    Demo().run()
