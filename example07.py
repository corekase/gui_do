import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, set_backdrop, load_font, set_font
from gui import add, set_cursor, set_buffered, restore_pristine, Canvas, CKind
from gui import GKind, Label, Button, Window, centre, ToggleButton, Scrollbar, Image
from gui import Frame, FrState, colours, PushButtonGroup, set_grid_properties, gridded

class Demo:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # screen rect
        self.screen_rect = self.screen.get_rect()
        # set window caption
        pygame.display.set_caption('gui_do')
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        # create a gui manager
        self.gui = gui_init(self.screen)
        # don't save overdrawn bitmaps into a buffer automatically, and don't use undraw_gui()
        set_buffered(False)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # load fonts
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # main label
        set_font('gui_do')
        add(Label((50, 50),'gui_do'))
        set_font('normal')
        # add a frame as a backdrop behind the screen content widgets
        add(Frame('backdrop', Rect(1570, 30, 320, 360)))
        # add content widgets
        self.make_scrollbars(1580, 40, 'screen')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'), self.exit)
        # setup for the togglebuttons
        set_grid_properties((85, 1050), 120, 20, 4)
        # control whether the background boxes are drawn
        self.boxes_toggle = add(ToggleButton('boxes', gridded(0, 0), True, 'Boxes'))
        # control whether the background circles are drawn
        self.circles_toggle = add(ToggleButton('circles', gridded(1, 0), True, 'Circles'))
        # control whether the pushboxes window is visible
        self.push_box_toggle = add(ToggleButton('push_window', gridded(2, 0), True, 'Pushboxes'))
        # control whether the pushradios window is visible
        self.push_radio_toggle = add(ToggleButton('push_radio', gridded(3, 0), True, 'Pushradios'))
        # control whether the life window is visible
        self.push_life_toggle = add(ToggleButton('push_life', gridded(4, 0), True, 'Life'))
        # control whether the scrollbar window is visible
        self.push_scroll_toggle = add(ToggleButton('push_scroll', gridded(5, 0), True, 'Scrollbars'))
        # make the pushboxes window
        self.pb_win = Window('Pushboxes', (50, 150), (140, 110))
        set_grid_properties((10, 10), 120, 20, 2)
        add(PushButtonGroup('pb1', gridded(0, 0), 'Pushbox', 'pb1', 0))
        add(PushButtonGroup('pb2', gridded(0, 1), 'Pushbox', 'pb1', 0))
        add(PushButtonGroup('pb3', gridded(0, 2), 'Pushbox', 'pb1', 0))
        add(Button('b1', gridded(0, 3), 'Button'))
        # make the pushradios window
        self.pr_win = Window('Pushradios', (50, 290), (140, 110))
        set_grid_properties((10, 10), 120, 20, 2)
        add(PushButtonGroup('pb4', gridded(0, 0), 'Pushradio', 'pb2', 1))
        add(PushButtonGroup('pb5', gridded(0, 1), 'Pushradio', 'pb2', 1))
        add(PushButtonGroup('pb6', gridded(0, 2), 'Pushradio', 'pb2', 1))
        add(Button('b2', gridded(0, 3), 'Button'))
        # make the Conway's Game of Life window
        width, height = 500, 500
        self.life_win = Window('Conway\'s Game of Life', (50, 430), (width, height))
        self.canvas = add(Canvas('life', Rect(10, 10, width - 20, height - 50), canvas_callback=self.handle_canvas, automatic_pristine=True))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_size()
        # a set to hold cell coordinates as tuples of x and y
        self.life = set()
        # toggle whether or not the simulation is processing
        self.toggle_life = add(ToggleButton('run', Rect(10, height - 30, 120, 20), False, 'Stop', 'Start'))
        # clicking this button resets the simulation to a default state, uses a callback function
        add(Button('reset', Rect(140, height - 30, 120, 20), 'Reset', self.reset))
        # reset the state of the simulation
        self.reset()
        # whether or not dragging with the right-mouse button over the canvas is active
        self.dragging = False
        # make the scrollbar window
        width, height = 320, 362
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        self.sb_win = Window('Scrollbar Styles', (window_x, window_y), (width, height))
        # add content widgets, but this time the window is the active object
        self.make_scrollbars(10, 10, 'window')
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # number of boxes and their size
        boxes = 50
        boxes_size = 12
        # get a list of positions
        boxes_position_list = self.make_position_list(boxes, boxes_size)
        # setup a frame to draw on our surface
        frame = Frame('none', Rect(0, 0, boxes_size, boxes_size))
        frame.state = FrState.Armed
        # create our bitmap
        frame_bitmap = pygame.surface.Surface((boxes_size, boxes_size))
        # point the frame object at it
        frame.surface = frame_bitmap
        # and render onto that surface
        frame.draw()
        # number of circles and their size
        circles = 50
        circles_size = 12
        # get a position list for them
        circles_position_list = self.make_position_list(circles, circles_size)
        # make a bitmap for them
        from gui.bitmapfactory import BitmapFactory
        factory = BitmapFactory()
        circle_bitmap = factory.draw_radio_checked_bitmap(circles_size, colours['full'], colours['none'])

        while self.running:
            # restore the pristine area to the screen before drawing
            restore_pristine()
            # if the mouse isn't over the canvas then end the dragging state
            if not self.canvas.focused():
                self.dragging = False
            # draw the boxes and circles if their toggles are pushed
            if self.boxes_toggle.read():
                boxes_position_list = self.draw_update_position_list(boxes_position_list, boxes_size, frame_bitmap)
            if self.circles_toggle.read():
                circles_position_list = self.draw_update_position_list(circles_position_list, circles_size, circle_bitmap)
            # update the visible windows
            self.pb_win.set_visible(self.push_box_toggle.read())
            self.pr_win.set_visible(self.push_radio_toggle.read())
            self.life_win.set_visible(self.push_life_toggle.read())
            self.sb_win.set_visible(self.push_scroll_toggle.read())
            # handle events
            self.handle_events()
            # draw current life cycle to the canvas
            self.draw_life()
            # generate a new cycle if the togglebutton is pressed
            if self.toggle_life.read():
                self.generate()
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
        # release resources
        pygame.quit()

    def handle_events(self):
        # update internal gui timers
        self.gui.timers.update()
        # handle the pygame event queue
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
                pass
                # if event.widget_id == 'widget_id':
                #     pass
                # elif event.widget_id == 'next_id':
                #     pass
            elif event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # handle escape key
                    self.running = False

    # make a random list of positions
    def make_position_list(self, num_items, size):
        positions = []
        for _ in range(num_items):
            x = randrange(0, self.screen_rect.width - (size * 2))
            y = randrange(0, self.screen_rect.height - (size * 2))
            dx = randrange(2, 7)
            dy = randrange(2, 7)
            if choice([True, False]):
                dx = -dx
            if choice([True, False]):
                dy = -dy
            positions.append((x, y, dx, dy))
        return positions

    # update the position and draw a bitmap at the position
    def draw_update_position_list(self, positions, size, bitmap):
        new_positions = []
        for x, y, dx, dy in positions:
            x += dx
            y += dy
            if x < 0 or x > self.screen_rect.width - size:
                dx = -dx
            if y < 0 or y > self.screen_rect.height - size:
                dy = -dy
            self.screen.blit(bitmap, (x, y))
            new_positions += [(x, y, dx, dy)]
        return new_positions

    # constuct some widgets, not saving any of the references that add() returns
    def make_scrollbars(self, x, y, prefix):
        add(Scrollbar(f'{prefix}a', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 0))
        y += 22
        add(Scrollbar(f'{prefix}b', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 1))
        y += 22
        add(Scrollbar(f'{prefix}c', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 2))
        y += 22
        add(Scrollbar(f'{prefix}d', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 3))
        y += 24
        add(Scrollbar(f'{prefix}e', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 0))
        x += 22
        add(Scrollbar(f'{prefix}f', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 1))
        x += 22
        add(Scrollbar(f'{prefix}g', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 2))
        x += 22
        add(Scrollbar(f'{prefix}h', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 3))
        add(Image('realize', Rect(x + 25, y, 210, 210), 'realize.png', False))
        set_font('gui_do')
        add(Label((x + 40, y + 210), 'Scrollbars!'))
        set_font('normal')

    # reset the life simulation to a default state
    def reset(self):
        self.origin_x = self.canvas_rect.centerx
        self.origin_y = self.canvas_rect.centery
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
        for cell in self.life:
            # Unpack x and y cell coordinates
            xpos, ypos = cell
            # calculate the graphical coordinate of the cell
            xpos = self.origin_x + (xpos * self.cell_size)
            ypos = self.origin_y + (ypos * self.cell_size)
            # Check to see if the cell is on screen and if so draw it
            bounded = (xpos >= 0) and (xpos <= self.canvas_rect.width) and \
                      (ypos >= 0) and (ypos <= self.canvas_rect.height)
            if bounded:
                self.canvas_surface.fill(colours['full'], Rect(xpos, ypos, self.cell_size - 1, self.cell_size - 1))

    # callback function
    def exit(self):
        self.running = False

    # callback function
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
                    x = CEvent.rel[0]
                    y = CEvent.rel[1]
                    self.origin_x = self.origin_x + x
                    self.origin_y = self.origin_y + y
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
