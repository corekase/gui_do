import sys
import pygame
from random import randrange, choice
from pygame import Color, Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, Window, set_pristine, set_font, set_cursor, restore_pristine
from gui import colours, set_grid_properties, gridded
from gui import GKind, Canvas, CKind, Label, Button, ButtonGroup, Toggle, Scrollbar, Image, Scheduler

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
        fonts = (('titlebar', 'Ubuntu-B.ttf', 14), ('normal', 'Gimbot.ttf', 16),
                 ('scroll', 'Gimbot.ttf', 32), ('gui_do', 'Gimbot.ttf', 72))
        self.gui = gui_init(self.screen, fonts)
        # blit a background image to the screen surface
        set_pristine('backdrop.jpg')
        # screen label
        set_font('gui_do')
        add(Label((50, 30), 'gui_do', True))
        set_font('normal')
        widget_height = 28
        # exit button
        add(Button('exit', Rect(10, 1042, 70, widget_height), 1, 'Exit'))
        # setup for the togglebuttons
        set_grid_properties((85, 1042), 120, widget_height, 4)
        # control whether the background circles are drawn
        self.circles_toggle = add(Toggle('circles', gridded(0, 0), 0, False, 'Circles'))
        # control whether the buttons and toggles window is visible
        self.buttons_toggle = add(Toggle('buttons_window', gridded(1, 0), 0, False, 'Buttons'))
        # control whether the scrollbar window is visible
        self.scrollbars_toggle = add(Toggle('scrollbar_window', gridded(2, 0), 0, False, 'Scrollbars'))
        # control whether the life window is visible
        self.life_toggle = add(Toggle('life_window', gridded(3, 0), 0, False, 'Life'))
        # control whether the Mandelbrot window is visible
        self.mandel_toggle = add(Toggle('mandel_window', gridded(4, 0), 0, False, 'Mandelbrot'))
        # make the button groups, buttons, and toggles window
        x_pos, y_pos = 50, 150
        set_grid_properties((10, 10), 120, widget_height, 2)
        self.button_group_win = add(Window('Button Groups, Buttons, and Toggles',
                                       (x_pos, y_pos), (gridded(7, 0).right + 10, gridded(0, 6).bottom)))
        add(Label(gridded(0, 0), 'G1 Boxed', True))
        add(Label(gridded(1, 0), 'G2 Rounded', True))
        add(Label(gridded(2, 0), 'G3 Angled', True))
        add(Label(gridded(3, 0), 'G4 Radioed', True))
        add(Label(gridded(4, 0), 'G5 Checked', True))
        add(Label(gridded(5, 0), 'G6 Mixed', True))
        add(Label(gridded(6, 0), 'Buttons', True))
        add(Label(gridded(7, 0), 'Toggles', True))
        lbg1 = add(ButtonGroup('bg1', 'bg1b01', gridded(0, 1), 0, 'Box 1'))
        add(ButtonGroup('bg1', 'bg1b02', gridded(0, 2), 0, 'Box 2',))
        add(ButtonGroup('bg1', 'bg1b03', gridded(0, 3), 0, 'Box 3',))
        add(ButtonGroup('bg1', 'bg1b04', gridded(0, 4), 0, 'Box 4',))
        add(ButtonGroup('bg1', 'bg1b05', gridded(0, 5), 0, 'Box 5',))
        lbg2 = add(ButtonGroup('bg2', 'bg2b01', gridded(1, 1), 1, 'Round 1'))
        add(ButtonGroup('bg2', 'bg2b02', gridded(1, 2), 1, 'Round 2'))
        add(ButtonGroup('bg2', 'bg2b03', gridded(1, 3), 1, 'Round 3'))
        add(ButtonGroup('bg2', 'bg2b04', gridded(1, 4), 1, 'Round 4'))
        add(ButtonGroup('bg2', 'bg2b05', gridded(1, 5), 1, 'Round 5'))
        lbg3 = add(ButtonGroup('bg3', 'bg3b01', gridded(2, 1), 2, 'Angle 1'))
        add(ButtonGroup('bg3', 'bg3b02', gridded(2, 2), 2, 'Angle 2'))
        add(ButtonGroup('bg3', 'bg3b03', gridded(2, 3), 2, 'Angle 3'))
        add(ButtonGroup('bg3', 'bg3b04', gridded(2, 4), 2, 'Angle 4'))
        add(ButtonGroup('bg3', 'bg3b05', gridded(2, 5), 2, 'Angle 5'))
        lbg4= add(ButtonGroup('bg4', 'bg4b01', gridded(3, 1), 3, 'Radio 1'))
        add(ButtonGroup('bg4', 'bg4b02', gridded(3, 2), 3, 'Radio 2'))
        add(ButtonGroup('bg4', 'bg4b03', gridded(3, 3), 3, 'Radio 3'))
        add(ButtonGroup('bg4', 'bg4b04', gridded(3, 4), 3, 'Radio 4'))
        add(ButtonGroup('bg4', 'bg4b05', gridded(3, 5), 3, 'Radio 5'))
        lbg5 = add(ButtonGroup('bg5', 'bg5b01', gridded(4, 1), 4, 'Check 1'))
        add(ButtonGroup('bg5', 'bg5b02', gridded(4, 2), 4, 'Check 2'))
        add(ButtonGroup('bg5', 'bg5b03', gridded(4, 3), 4, 'Check 3'))
        add(ButtonGroup('bg5', 'bg5b04', gridded(4, 4), 4, 'Check 4'))
        add(ButtonGroup('bg5', 'bg5b05', gridded(4, 5), 4, 'Check 5'))
        lbg6 = add(ButtonGroup('bg6', 'bg6b01', gridded(5, 1), 0, 'Mix 1'))
        add(ButtonGroup('bg6', 'bg6b02', gridded(5, 2), 1, 'Mix 2'))
        add(ButtonGroup('bg6', 'bg6b03', gridded(5, 3), 2, 'Mix 3'))
        add(ButtonGroup('bg6', 'bg6b04', gridded(5, 4), 3, 'Mix 4'))
        add(ButtonGroup('bg6', 'bg6b05', gridded(5, 5), 4, 'Mix 5'))
        add(Button('b1', gridded(6, 1), 0, 'Button 1'))
        add(Button('b2', gridded(6, 2), 1, 'Button 2'))
        add(Button('b3', gridded(6, 3), 2, 'Button 3'))
        add(Button('b4', gridded(6, 4), 3, 'Button 4'))
        add(Button('b5', gridded(6, 5), 4, 'Button 5'))
        add(Toggle('t1', gridded(7, 1), 0, False, 'Push 1', 'Raise 1'))
        add(Toggle('t2', gridded(7, 2), 1, False, 'Push 2', 'Raise 2'))
        add(Toggle('t3', gridded(7, 3), 2, False, 'Push 3', 'Raise 3'))
        add(Toggle('t4', gridded(7, 4), 3, False, 'Push 4', 'Raise 4'))
        add(Toggle('t5', gridded(7, 5), 4, False, 'Push 5', 'Raise 5'))
        set_grid_properties((10, gridded(0, 5).bottom + 4), 122, widget_height, 0, False)
        self.label1 = add(Label(gridded(0, 0), f'ID: {lbg1.read_id()}', True))
        self.label2 = add(Label(gridded(1, 0), f'ID: {lbg2.read_id()}', True))
        self.label3 = add(Label(gridded(2, 0), f'ID: {lbg3.read_id()}', True))
        self.label4 = add(Label(gridded(3, 0), f'ID: {lbg4.read_id()}', True))
        self.label5 = add(Label(gridded(4, 0), f'ID: {lbg5.read_id()}', True))
        self.label6 = add(Label(gridded(5, 0), f'ID: {lbg6.read_id()}', True))
        # make the scrollbar window
        y_pos += 248
        self.scrollbar_win = add(Window('Scrollbars', (x_pos, y_pos), (320, 362)))
        x = y = 10
        add(Scrollbar(f'scrollbar_a', Rect(x, y, 300, 20), 0, (100, 0, 30, 10), True))
        y += 22
        add(Scrollbar(f'scrollbar_b', Rect(x, y, 300, 20), 1, (100, 0, 30, 10), True))
        y += 22
        add(Scrollbar(f'scrollbar_c', Rect(x, y, 300, 20), 2, (100, 0, 30, 10), True))
        y += 22
        add(Scrollbar(f'scrollbar_d', Rect(x, y, 300, 20), 3, (100, 0, 30, 10), True))
        y += 24
        add(Scrollbar(f'scrollbar_e', Rect(x, y, 20, 250), 0, (100, 0, 30, 10), False))
        x += 22
        add(Scrollbar(f'scrollbar_f', Rect(x, y, 20, 250), 1, (100, 0, 30, 10), False))
        x += 22
        add(Scrollbar(f'scrollbar_g', Rect(x, y, 20, 250), 2, (100, 0, 30, 10), False))
        x += 22
        add(Scrollbar(f'scrollbar_h', Rect(x, y, 20, 250), 3, (100, 0, 30, 10), False))
        add(Image('realize', Rect(x + 25, y, 210, 210), 'realize.png', False))
        set_font('scroll')
        add(Label((x + 30, y + 215), 'Scrollbars!', True))
        set_font('normal')
        # make the Conway's Game of Life window
        x_pos += 327
        width, height = 600, 600
        self.life_win = add(Window('Conway\'s Game of Life', (x_pos, y_pos), (width, height)))
        self.canvas = add(Canvas('life', Rect(10, 10, width - 20, height - (widget_height * 2)), canvas_callback=self.handle_canvas, automatic_pristine=True))
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_size()
        # a set to hold cell coordinates as tuples of x and y
        self.life = set()
        set_grid_properties((10, height - widget_height - 10), 100, widget_height, 2)
        # resets the life simulation to a default state, uses a callback function
        add(Button('life_reset', gridded(0, 0), 2, 'Reset'), self.life_reset)
        # toggle whether or not the simulation is processing
        self.toggle_life = add(Toggle('run', gridded(1, 0), 3, False, 'Stop', 'Start'))
        width, height = 600, 600
        pos = x_pos + 607, y_pos
        mandel_overall = Rect(10, 10, width - 20, height - (widget_height * 2))
        self.mandel_win = add(Window('Mandelbrot', pos, (width, height)))
        self.mandel_canvas = add(Canvas('mandel', mandel_overall))
        self.gui.hide_widgets(self.mandel_canvas)
        self.mandel_canvas_rect = self.mandel_canvas.get_size()
        cx, cy, cwidth, cheight = self.mandel_canvas.get_size()
        chalfx, chalfy = (cwidth - 20) // 2, (cheight - 20) // 2
        self.canvas1 = add(Canvas('can1', Rect(10, 10, chalfx + 10, chalfy + 10)))
        self.canvas2 = add(Canvas('can2', Rect(13 + chalfx + 5, 10, chalfx + 10, chalfy + 10)))
        self.canvas3 = add(Canvas('can3', Rect(10, 13 + chalfy + 5, chalfx + 10, chalfy + 10)))
        self.canvas4 = add(Canvas('can4', Rect(13 + chalfx + 5, 13 + chalfy + 5, chalfx + 10, chalfy + 10)))
        self.gui.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
        self.clear_mandel_surfaces()
        set_grid_properties((10, height - widget_height - 10), int((600 - 30) / 5), widget_height, 2)
        add(Button('mandel_reset', gridded(0, 0), 2, 'Reset'))
        add(Button('iterative', gridded(1, 0), 1, 'Iterative'))
        add(Button('recursive', gridded(2, 0), 1, 'Recursive'))
        add(Button('1split', gridded(3, 0), 1, '1M 4 Tasks'))
        add(Button('4split', gridded(4, 0), 1, '4M 4 Tasks'))
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # reset the state of the simulation
        self.life_reset()
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
        circle_bitmap_b = factory.draw_radio_bitmap(self.size, colours['medium'], colours['none'])
        # make position list for circles
        for _ in range(circles):
            x = randrange(self.size, self.screen_rect.width - (self.size * 2))
            y = randrange(self.size, self.screen_rect.height - (self.size * 2))
            dx = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            dy = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            self.positions.append((x, y, dx, dy, choice([circle_bitmap_a, circle_bitmap_b])))
        self.scheduler = Scheduler()
        self.running = True

    def run(self):
        self.scheduler.run_scheduler(self.preamble, self.handle_events, self.postamble)

    def preamble(self):
        # restore the pristine area to the screen before drawing
        restore_pristine()
        # if the mouse isn't over the canvas then end the dragging state
        if not self.canvas.focused():
            self.dragging = False
        # draw the circles if their toggle is pushed
        if self.circles_toggle.read():
            self.update_circles(self.size)
        # update the visible windows
        self.button_group_win.set_visible(self.buttons_toggle.read())
        self.scrollbar_win.set_visible(self.scrollbars_toggle.read())
        self.life_win.set_visible(self.life_toggle.read())
        self.mandel_win.set_visible(self.mandel_toggle.read())

    def handle_events(self, event):
        # handle events
        if event.type == GKind.Widget:
            if event.widget_id == 'exit':
                # exit button was clicked
                self.running = False
            elif event.widget_id == 'mandel_reset':
                self.scheduler.remove_tasks('iter', 'recu', '1', '2', '3', '4', 'can1', 'can2', 'can3', 'can4')
                self.gui.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                self.gui.show_widgets(self.mandel_canvas)
                self.clear_mandel_surfaces()
            elif not self.scheduler.tasks_active():
                if event.widget_id == 'iterative':
                    self.gui.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.gui.show_widgets(self.mandel_canvas)
                    self.clear_mandel_surfaces()
                    x, y, w, h = self.mandel_canvas_rect
                    self.mandel_setup(w, h)
                    self.scheduler.add_task('iter', self.mandel_iterative)
                elif event.widget_id == 'recursive':
                    self.gui.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.gui.show_widgets(self.mandel_canvas)
                    self.clear_mandel_surfaces()
                    x, y, w, h = self.mandel_canvas_rect
                    self.mandel_setup(w, h)
                    self.scheduler.add_task('recu', self.mandel_recursive, (self.mandel_canvas_rect, self.mandel_canvas.canvas))
                elif event.widget_id == '1split':
                    self.gui.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.gui.show_widgets(self.mandel_canvas)
                    self.clear_mandel_surfaces()
                    x, y, w, h = self.mandel_canvas_rect
                    self.mandel_setup(w, h)
                    hx, hy = w // 2, h // 2
                    self.scheduler.add_task('1', self.mandel_recursive, (Rect(0, 0, hx, hy), self.mandel_canvas.canvas))
                    self.scheduler.add_task('2', self.mandel_recursive, (Rect(hx, y, hx, hy), self.mandel_canvas.canvas))
                    self.scheduler.add_task('3', self.mandel_recursive, (Rect(x, hy, hx, hy), self.mandel_canvas.canvas))
                    self.scheduler.add_task('4', self.mandel_recursive, (Rect(hx, hy, hx, hy), self.mandel_canvas.canvas))
                elif event.widget_id == '4split':
                    self.gui.hide_widgets(self.mandel_canvas)
                    self.gui.show_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.clear_mandel_surfaces()
                    _, _, w1, h1 = self.mandel_canvas.get_size()
                    w1 = w1 // 2
                    h1 = h1 // 2
                    self.mandel_setup(w1, h1)
                    self.scheduler.add_task('can1', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas1.canvas))
                    self.scheduler.add_task('can2', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas2.canvas))
                    self.scheduler.add_task('can3', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas3.canvas))
                    self.scheduler.add_task('can4', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas4.canvas))
        elif event.type == GKind.Group:
            if event.group == 'bg1':
                self.label1.set_label(f'ID: {event.widget_id}')
            elif event.group == 'bg2':
                self.label2.set_label(f'ID: {event.widget_id}')
            elif event.group == 'bg3':
                self.label3.set_label(f'ID: {event.widget_id}')
            elif event.group == 'bg4':
                self.label4.set_label(f'ID: {event.widget_id}')
            elif event.group == 'bg5':
                self.label5.set_label(f'ID: {event.widget_id}')
            elif event.group == 'bg6':
                self.label6.set_label(f'ID: {event.widget_id}')
        elif event.type == GKind.KeyDown:
            if event.key == K_ESCAPE:
                # escape key pressed
                self.running = False
        elif event.type == GKind.Quit:
            # window close widget or alt-f4 keypress
            self.running = False

    def postamble(self):
        if not self.running:
            # release resources
            pygame.quit()
            # exit python
            sys.exit(0)
        # if the life window is visible then handle it
        if self.life_win.get_visible():
            # generate a new cycle if the togglebutton is pressed
            if self.toggle_life.read():
                self.generate()
            # draw life cells on the canvas
            self.draw_life()

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
    def life_reset(self):
        self.origin_x, self.origin_y = self.canvas_rect.centerx, self.canvas_rect.centery
        self.cell_size = 6
        self.toggle_life.set(False)
        # the starting configuration of the Life grid
        self.life = set({(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)})

    # Coordinates around a cell, given as a delta table
    neighbours = ((-1, -1), (-1,  0), (-1, 1), (0, -1),
                  ( 0,  1), ( 1, -1), ( 1, 0), (1,  1))
    # function to generate a cycle of life
    def generate(self):
        def population(cell):
            count = 0
            # For the delta table entries generate tuples of (x, y) and
            # then test them for membership in the life set
            for position in Demo.neighbours:
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
            for new_cell in Demo.neighbours:
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

    def clear_mandel_surfaces(self):
        self.mandel_canvas.canvas.fill(colours['medium'])
        self.canvas1.canvas.fill(colours['medium'])
        self.canvas2.canvas.fill(colours['medium'])
        self.canvas3.canvas.fill(colours['medium'])
        self.canvas4.canvas.fill(colours['medium'])

    def mandel_setup(self, width, height):
        self.max_iter = 128
        self.maximum_iters = self.max_iter - 1
        self.mandel_width, self.mandel_height = width, height
        self.center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        self.scale = max((extent / self.mandel_width).real, (extent / self.mandel_height).imag)

    def mandel_iterative(self, id):
        for y in range(self.mandel_height):
            for x in range(self.mandel_width):
                self.mandel_canvas.canvas.set_at((x, y), self.col(self.pixel(x, y)))
                if self.scheduler.task_time(id):
                    yield

    def mandel_recursive(self, id, item):
        x, y, w, h = item[0]
        canvas = item[1]
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
            canvas.fill(self.col(top_left), Rect(x, y, w, h))
            return
        if w > 2 or h > 2:
            half_x = (w + (w % 2)) // 2
            half_y = (h + (h % 2)) // 2
            if self.scheduler.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x, y, half_x, half_y), canvas))
            if self.scheduler.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x + half_x, y, half_x, half_y), canvas))
            if self.scheduler.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x + half_x, y + half_y, half_x, half_y), canvas))
            if self.scheduler.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x, y + half_y, half_x, half_y), canvas))
            return
        else:
            r, b = item[0].right - 1, item[0].bottom - 1
            top_right, bottom_left, bottom_right = self.pixel(r, y), self.pixel(x, b), self.pixel(r, b)
            canvas.lock()
            canvas.set_at((x, y), self.col(top_left))
            canvas.set_at((x + 1, y), self.col(top_right))
            canvas.set_at((x, y + 1), self.col(bottom_left))
            canvas.set_at((x + 1, y + 1), self.col(bottom_right))
            canvas.unlock()
            return

    def pixel(self, x, y):
        c = self.center + (x - self.mandel_width // 2 + (y - self.mandel_height // 2) * 1j) * self.scale
        z = 0
        for k in range(self.max_iter):
            z = z ** 2 + c
            if (z * z.conjugate()).real > 4.0:
                break
        return k

    cols = (Color(66, 30, 15), Color(25, 7, 26), Color(9, 1, 47), Color(4, 4, 73),
            Color(0, 7, 100), Color(12, 44, 138), Color(24, 82, 177), Color(57, 125, 209),
            Color(134, 181, 229), Color(211, 236, 248), Color(241, 233, 191), Color(248, 201, 95),
            Color(255, 170, 0), Color(204, 128, 0), Color(153, 87, 0), Color(106, 52, 3))

    def col(self, k):
        if k == self.maximum_iters:
            return Color(0, 0, 0)
        else:
            return Demo.cols[k % 16]

if __name__ == '__main__':
    Demo().run()
