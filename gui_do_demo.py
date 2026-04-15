import sys
import pygame
from random import randrange, choice
from pygame import Color, Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import GuiManager, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle, Engine, StateManager
from gui import colours

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
        # -----------------------
        # begin gui setup
        # -----------------------
        fonts = (('titlebar', 'Ubuntu-B.ttf', 14), ('normal', 'Gimbot.ttf', 16),
                 ('scroll', 'Gimbot.ttf', 32), ('gui_do', 'Gimbot.ttf', 72))
        # -----------------------
        # begin gui1
        # -----------------------
        # create a gui manager
        g1 = GuiManager(self.screen, fonts)
        self.s1 = g1.scheduler
        b1 = g1.bitmap_factory
        w1 = g1.widget_dispatcher
        # blit a background image to the screen surface
        g1.set_pristine('backdrop.jpg')
        # screen label
        b1.set_font('gui_do')
        w1.label((50, 30), 'gui_do', True)
        b1.set_font('normal')
        widget_height = 28
        # exit button
        w1.button('exit', Rect(10, 1042, 70, widget_height), ButtonStyle.Angle, 'Exit')
        # setup for the togglebuttons
        g1.set_grid_properties((85, 1042), 120, widget_height, 4)
        # switch to gui2 button
        self.gui2_Button = w1.button('gui2', g1.gridded(0, 0), ButtonStyle.Round, 'GUI 2')
        # control whether the background circles are drawn
        self.circles_Toggle = w1.toggle('circles', g1.gridded(1, 0), ButtonStyle.Round, False, 'Circles')
        # control whether the buttons and toggles window is visible
        self.Buttons_Toggle = w1.toggle('Buttons_Window', g1.gridded(2, 0), ButtonStyle.Round, False, 'Buttons')
        # control whether the scrollbar window is visible
        self.Scrollbars_Toggle = w1.toggle('Scrollbar_Window', g1.gridded(3, 0), ButtonStyle.Round, False, 'Scrollbars')
        # control whether the life window is visible
        self.life_Toggle = w1.toggle('life_Window', g1.gridded(4, 0), ButtonStyle.Round, False, 'Life')
        # control whether the Mandelbrot window is visible
        self.mandel_Toggle = w1.toggle('mandel_Window', g1.gridded(5, 0), ButtonStyle.Round, False, 'Mandelbrot')
        # make the button groups, buttons, and toggles window
        x_pos, y_pos = 50, 150
        g1.set_grid_properties((10, 10), 120, widget_height, 2)
        self.Button_group_win = w1.window('Button Groups, Buttons, and Toggles',
                                          (x_pos, y_pos), (g1.gridded(7, 0).right + 10, g1.gridded(0, 6).bottom))
        w1.label(g1.gridded(0, 0), 'G1 Boxed', True)
        w1.label(g1.gridded(1, 0), 'G2 Rounded', True)
        w1.label(g1.gridded(2, 0), 'G3 Angled', True)
        w1.label(g1.gridded(3, 0), 'G4 Radioed', True)
        w1.label(g1.gridded(4, 0), 'G5 Checked', True)
        w1.label(g1.gridded(5, 0), 'G6 Mixed', True)
        w1.label(g1.gridded(6, 0), 'Buttons', True)
        w1.label(g1.gridded(7, 0), 'Toggles', True)
        lbg1 = w1.buttongroup('bg1', 'bg1b01', g1.gridded(0, 1), ButtonStyle.Box, 'Box 1')
        w1.buttongroup('bg1', 'bg1b02', g1.gridded(0, 2), ButtonStyle.Box, 'Box 2',)
        w1.buttongroup('bg1', 'bg1b03', g1.gridded(0, 3), ButtonStyle.Box, 'Box 3',)
        w1.buttongroup('bg1', 'bg1b04', g1.gridded(0, 4), ButtonStyle.Box, 'Box 4',)
        w1.buttongroup('bg1', 'bg1b05', g1.gridded(0, 5), ButtonStyle.Box, 'Box 5',)
        lbg2 = w1.buttongroup('bg2', 'bg2b01', g1.gridded(1, 1), ButtonStyle.Round, 'Round 1')
        w1.buttongroup('bg2', 'bg2b02', g1.gridded(1, 2), ButtonStyle.Round, 'Round 2')
        w1.buttongroup('bg2', 'bg2b03', g1.gridded(1, 3), ButtonStyle.Round, 'Round 3')
        w1.buttongroup('bg2', 'bg2b04', g1.gridded(1, 4), ButtonStyle.Round, 'Round 4')
        w1.buttongroup('bg2', 'bg2b05', g1.gridded(1, 5), ButtonStyle.Round, 'Round 5')
        lbg3 = w1.buttongroup('bg3', 'bg3b01', g1.gridded(2, 1), ButtonStyle.Angle, 'Angle 1')
        w1.buttongroup('bg3', 'bg3b02', g1.gridded(2, 2), ButtonStyle.Angle, 'Angle 2')
        w1.buttongroup('bg3', 'bg3b03', g1.gridded(2, 3), ButtonStyle.Angle, 'Angle 3')
        w1.buttongroup('bg3', 'bg3b04', g1.gridded(2, 4), ButtonStyle.Angle, 'Angle 4')
        w1.buttongroup('bg3', 'bg3b05', g1.gridded(2, 5), ButtonStyle.Angle, 'Angle 5')
        lbg4 = w1.buttongroup('bg4', 'bg4b01', g1.gridded(3, 1), ButtonStyle.Radio, 'Radio 1')
        w1.buttongroup('bg4', 'bg4b02', g1.gridded(3, 2), ButtonStyle.Radio, 'Radio 2')
        w1.buttongroup('bg4', 'bg4b03', g1.gridded(3, 3), ButtonStyle.Radio, 'Radio 3')
        w1.buttongroup('bg4', 'bg4b04', g1.gridded(3, 4), ButtonStyle.Radio, 'Radio 4')
        w1.buttongroup('bg4', 'bg4b05', g1.gridded(3, 5), ButtonStyle.Radio, 'Radio 5')
        lbg5 = w1.buttongroup('bg5', 'bg5b01', g1.gridded(4, 1), ButtonStyle.Check, 'Check 1')
        w1.buttongroup('bg5', 'bg5b02', g1.gridded(4, 2), ButtonStyle.Check, 'Check 2')
        w1.buttongroup('bg5', 'bg5b03', g1.gridded(4, 3), ButtonStyle.Check, 'Check 3')
        w1.buttongroup('bg5', 'bg5b04', g1.gridded(4, 4), ButtonStyle.Check, 'Check 4')
        w1.buttongroup('bg5', 'bg5b05', g1.gridded(4, 5), ButtonStyle.Check, 'Check 5')
        lbg6 = w1.buttongroup('bg6', 'bg6b01', g1.gridded(5, 1), ButtonStyle.Box, 'Mix 1')
        w1.buttongroup('bg6', 'bg6b02', g1.gridded(5, 2), ButtonStyle.Round, 'Mix 2')
        w1.buttongroup('bg6', 'bg6b03', g1.gridded(5, 3), ButtonStyle.Angle, 'Mix 3')
        w1.buttongroup('bg6', 'bg6b04', g1.gridded(5, 4), ButtonStyle.Radio, 'Mix 4')
        w1.buttongroup('bg6', 'bg6b05', g1.gridded(5, 5), ButtonStyle.Check, 'Mix 5')
        w1.button('b1', g1.gridded(6, 1), ButtonStyle.Box, 'Button 1')
        w1.button('b2', g1.gridded(6, 2), ButtonStyle.Round, 'Button 2')
        w1.button('b3', g1.gridded(6, 3), ButtonStyle.Angle, 'Button 3')
        w1.button('b4', g1.gridded(6, 4), ButtonStyle.Radio, 'Button 4')
        w1.button('b5', g1.gridded(6, 5), ButtonStyle.Check, 'Button 5')
        w1.toggle('t1', g1.gridded(7, 1), ButtonStyle.Box, False, 'Push 1', 'Raise 1')
        w1.toggle('t2', g1.gridded(7, 2), ButtonStyle.Round, False, 'Push 2', 'Raise 2')
        w1.toggle('t3', g1.gridded(7, 3), ButtonStyle.Angle, False, 'Push 3', 'Raise 3')
        w1.toggle('t4', g1.gridded(7, 4), ButtonStyle.Radio, False, 'Push 4', 'Raise 4')
        w1.toggle('t5', g1.gridded(7, 5), ButtonStyle.Check, False, 'Push 5', 'Raise 5')
        g1.set_grid_properties((10, g1.gridded(0, 5).bottom + 4), 122, widget_height, 0, False)
        self.label1 = w1.label(g1.gridded(0, 0), f'ID: {lbg1.read_id()}', True)
        self.label2 = w1.label(g1.gridded(1, 0), f'ID: {lbg2.read_id()}', True)
        self.label3 = w1.label(g1.gridded(2, 0), f'ID: {lbg3.read_id()}', True)
        self.label4 = w1.label(g1.gridded(3, 0), f'ID: {lbg4.read_id()}', True)
        self.label5 = w1.label(g1.gridded(4, 0), f'ID: {lbg5.read_id()}', True)
        self.label6 = w1.label(g1.gridded(5, 0), f'ID: {lbg6.read_id()}', True)
        # make the scrollbar window
        y_pos += 248
        self.Scrollbar_win = w1.window('Scrollbars', (x_pos, y_pos), (320, 362))
        x = y = 10
        w1.scrollbar('Scrollbar_a', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Skip, (100, 0, 30, 10))
        y += 22
        w1.scrollbar('Scrollbar_b', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Split, (100, 0, 30, 10))
        y += 22
        w1.scrollbar('Scrollbar_c', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Near, (100, 0, 30, 10))
        y += 22
        w1.scrollbar('Scrollbar_d', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Far, (100, 0, 30, 10))
        y += 24
        w1.scrollbar('Scrollbar_e', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Skip, (100, 0, 30, 10))
        x += 22
        w1.scrollbar('Scrollbar_f', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Split, (100, 0, 30, 10))
        x += 22
        w1.scrollbar('Scrollbar_g', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Near, (100, 0, 30, 10))
        x += 22
        w1.scrollbar('Scrollbar_h', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Far, (100, 0, 30, 10))
        w1.image('realize', Rect(x + 25, y, 210, 210), 'realize.png', False)
        b1.set_font('scroll')
        w1.label((x + 30, y + 215), 'Scrollbars!', True)
        b1.set_font('normal')
        # make the Conway's Game of Life window
        x_pos += 327
        width, height = 600, 600
        self.life_win = w1.window('Conway\'s Game of Life', (x_pos, y_pos), (width, height))
        self.canvas = w1.canvas('life', Rect(10, 10, width - 20, height - (widget_height * 2)), canvas_callback=self.handle_Canvas, automatic_pristine=True)
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.get_size()
        # a set to hold cell coordinates as tuples of x and y
        self.life = set()
        g1.set_grid_properties((10, height - widget_height - 10), 100, widget_height, 2)
        # resets the life simulation to a default state, uses a callback function
        w1.button('life_reset', g1.gridded(0, 0), ButtonStyle.Angle, 'Reset')
        # toggle whether or not the simulation is processing
        self.Toggle_life = w1.toggle('run', g1.gridded(1, 0), ButtonStyle.Round, False, 'Stop', 'Start')
        width, height = 600, 600
        pos = x_pos + 607, y_pos
        mandel_overall = Rect(10, 10, width - 20, height - (widget_height * 2))
        self.mandel_win = w1.window('Mandelbrot', pos, (width, height))
        self.mandel_canvas = w1.canvas('mandel', mandel_overall)
        g1.hide_widgets(self.mandel_canvas)
        self.mandel_canvas_rect = self.mandel_canvas.get_size()
        cx, cy, cwidth, cheight = self.mandel_canvas.get_size()
        chalfx, chalfy = (cwidth - 20) // 2, (cheight - 20) // 2
        self.canvas1 = w1.canvas('can1', Rect(10, 10, chalfx + 10, chalfy + 10))
        self.canvas2 = w1.canvas('can2', Rect(13 + chalfx + 5, 10, chalfx + 10, chalfy + 10))
        self.canvas3 = w1.canvas('can3', Rect(10, 13 + chalfy + 5, chalfx + 10, chalfy + 10))
        self.canvas4 = w1.canvas('can4', Rect(13 + chalfx + 5, 13 + chalfy + 5, chalfx + 10, chalfy + 10))
        g1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
        self.clear_mandel_surfaces()
        g1.set_grid_properties((10, height - widget_height - 10), int((600 - 30) / 5), widget_height, 2)
        w1.button('mandel_reset', g1.gridded(0, 0), ButtonStyle.Angle, 'Reset')
        w1.button('iterative', g1.gridded(1, 0), ButtonStyle.Round, 'Iterative')
        w1.button('recursive', g1.gridded(2, 0), ButtonStyle.Round, 'Recursive')
        w1.button('1split', g1.gridded(3, 0), ButtonStyle.Round, '1M 4 Tasks')
        w1.button('4split', g1.gridded(4, 0), ButtonStyle.Round, '4M 4 Tasks')
        # set cursor image
        g1.set_cursor((1, 1), 'cursor.png')
        self.gui1 = g1
        # -----------------------
        # begin gui2
        # -----------------------
        g2 = GuiManager(self.screen, fonts)
        self.s2 = g2.scheduler
        g2.bitmap_factory.set_font('normal')
        w2 = g2.widget_dispatcher
        g2.set_pristine('backdrop.jpg')
        w2.button('return', Rect(10, 1042, 70, widget_height), ButtonStyle.Angle, 'Back')
        w2.window('GUI 2', (50, 150), (300, 300))
        # set cursor for gui2
        g2.set_cursor((1, 1), 'cursor.png')
        self.gui2 = g2
        # -----------------------
        # Setup Engine and StateManager
        # -----------------------
        self.state_manager = StateManager()

        # Register contexts with StateManager
        self.state_manager.register_context(
            'gui1',
            self.gui1,
            self.s1,
            self.gui1.timers,
            self.preamble1,
            self.handle_events1,
            self.postamble1
        )
        self.state_manager.register_context(
            'gui2',
            self.gui2,
            self.s2,
            self.gui2.timers,
            self.preamble2,
            self.handle_events2,
            self.postamble2
        )

        # Set initial context to gui1
        self.state_manager.switch_context('gui1')

        # Create the engine
        self.engine = Engine(self.state_manager)
        # -----------------------
        # end gui setup
        # -----------------------
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
        factory = g1.bitmap_factory
        circle_bitmap_a = factory.draw_radio_bitmap(self.size, colours['light'], colours['none'])
        circle_bitmap_b = factory.draw_radio_bitmap(self.size, colours['medium'], colours['none'])
        # make position list for circles
        for _ in range(circles):
            x = randrange(self.size, self.screen_rect.width - (self.size * 2))
            y = randrange(self.size, self.screen_rect.height - (self.size * 2))
            dx = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            dy = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            self.positions.append((x, y, dx, dy, choice([circle_bitmap_a, circle_bitmap_b])))

    def run(self):
        """Run the application using the Engine with StateManager contexts."""
        try:
            self.engine.run()
        finally:
            pygame.quit()
            sys.exit(0)

    def preamble1(self):
        # restore the pristine area to the screen before drawing
        self.gui1.restore_pristine()
        # if the mouse isn't over the canvas then end the dragging state
        if not self.canvas.focused():
            self.dragging = False
        # draw the circles if their toggle is pushed
        if self.circles_Toggle.read():
            self.update_circles(self.size)
        # update the visible windows
        self.Button_group_win.visible = self.Buttons_Toggle.read()
        self.Scrollbar_win.visible = self.Scrollbars_Toggle.read()
        self.life_win.visible = self.life_Toggle.read()
        self.mandel_win.visible = self.mandel_Toggle.read()

    def handle_events1(self, event):
        # handle events
        if event.type == Event.Widget:
            if event.widget_id == 'exit':
                # exit button was clicked
                self.state_manager.set_running(False)
            elif event.widget_id == 'gui2':
                # switch to gui2
                self.state_manager.switch_context('gui2')
            elif event.widget_id == 'life_reset':
                self.life_reset()
            elif event.widget_id == 'mandel_reset':
                self.s1.remove_tasks('iter', 'recu', '1', '2', '3', '4', 'can1', 'can2', 'can3', 'can4')
                self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                self.gui1.show_widgets(self.mandel_canvas)
                self.clear_mandel_surfaces()
            elif not self.s1.tasks_active():
                if event.widget_id == 'iterative':
                    self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.gui1.show_widgets(self.mandel_canvas)
                    self.clear_mandel_surfaces()
                    x, y, w, h = self.mandel_canvas_rect
                    self.mandel_setup(w, h)
                    self.s1.add_task('iter', self.mandel_iterative)
                elif event.widget_id == 'recursive':
                    self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.gui1.show_widgets(self.mandel_canvas)
                    self.clear_mandel_surfaces()
                    x, y, w, h = self.mandel_canvas_rect
                    self.mandel_setup(w, h)
                    self.s1.add_task('recu', self.mandel_recursive, (self.mandel_canvas_rect, self.mandel_canvas.canvas))
                elif event.widget_id == '1split':
                    self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.gui1.show_widgets(self.mandel_canvas)
                    self.clear_mandel_surfaces()
                    x, y, w, h = self.mandel_canvas_rect
                    self.mandel_setup(w, h)
                    hx, hy = w // 2, h // 2
                    self.s1.add_task('1', self.mandel_recursive, (Rect(0, 0, hx, hy), self.mandel_canvas.canvas))
                    self.s1.add_task('2', self.mandel_recursive, (Rect(hx, y, hx, hy), self.mandel_canvas.canvas))
                    self.s1.add_task('3', self.mandel_recursive, (Rect(x, hy, hx, hy), self.mandel_canvas.canvas))
                    self.s1.add_task('4', self.mandel_recursive, (Rect(hx, hy, hx, hy), self.mandel_canvas.canvas))
                elif event.widget_id == '4split':
                    self.gui1.hide_widgets(self.mandel_canvas)
                    self.gui1.show_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
                    self.clear_mandel_surfaces()
                    _, _, w1, h1 = self.mandel_canvas.get_size()
                    w1 = w1 // 2
                    h1 = h1 // 2
                    self.mandel_setup(w1, h1)
                    self.s1.add_task('can1', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas1.canvas))
                    self.s1.add_task('can2', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas2.canvas))
                    self.s1.add_task('can3', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas3.canvas))
                    self.s1.add_task('can4', self.mandel_recursive, (Rect(0, 0, w1, h1), self.canvas4.canvas))
        elif event.type == Event.Group:
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
        elif event.type == Event.KeyDown:
            if event.key == K_ESCAPE:
                # escape key pressed
                self.state_manager.set_running(False)
        elif event.type == Event.Quit:
            # window close widget or alt-f4 keypress
            self.state_manager.set_running(False)

    def postamble1(self):
        # restore the pristine area to the screen before drawing
        self.gui1.restore_pristine()
        # if the mouse isn't over the canvas then end the dragging state
        if not self.canvas.focused():
            self.dragging = False
        # draw the circles if their toggle is pushed
        if self.circles_Toggle.read():
            self.update_circles(self.size)
        # update the visible windows
        self.Button_group_win.visible = self.Buttons_Toggle.read()
        self.Scrollbar_win.visible = self.Scrollbars_Toggle.read()
        self.life_win.visible = self.life_Toggle.read()
        self.mandel_win.visible = self.mandel_Toggle.read()
        # if the life window is visible then handle it
        if self.life_win.visible:
            # generate a new cycle if the togglebutton is pressed
            if self.Toggle_life.read():
                self.generate()
            # draw life cells on the canvas
            self.draw_life()

    def preamble2(self):
        # restore the pristine area to the screen before drawing
        self.gui2.restore_pristine()

    def handle_events2(self, event):
        # handle events
        if event.type == Event.Widget:
            if event.widget_id == 'return':
                # return button was clicked
                self.state_manager.switch_context('gui1')
        elif event.type == Event.KeyDown:
            if event.key == K_ESCAPE:
                # escape key pressed
                self.state_manager.set_running(False)
        elif event.type == Event.Quit:
            # window close widget or alt-f4 keypress
            self.state_manager.set_running(False)

    def postamble2(self):
        # restore the pristine area to the screen before drawing
        self.gui2.restore_pristine()

    # Canvas callback function
    def handle_Canvas(self):
        # read the event from the canvas widget
        CEvent = self.canvas.read_event()
        if CEvent != None:
            # parse that event by kind and parameters
            if CEvent.type == CanvasEvent.MouseButtonDown:
                # right-mouse button pressed, enter dragging state
                if CEvent.button == 3:
                    self.dragging = True
            elif CEvent.type == CanvasEvent.MouseButtonUp:
                # right-mouse button released, exit dragging state
                if CEvent.button == 3:
                    self.dragging = False
            elif CEvent.type == CanvasEvent.MouseMotion:
                # if dragging then track relative position
                if self.dragging:
                    x, y = CEvent.rel[0], CEvent.rel[1]
                    self.origin_x += x
                    self.origin_y += y
            elif CEvent.type == CanvasEvent.MouseWheel:
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
        self.Toggle_life.set(False)
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
                if self.s1.task_time(id):
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
            if self.s1.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x, y, half_x, half_y), canvas))
            if self.s1.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x + half_x, y, half_x, half_y), canvas))
            if self.s1.task_time(id):
                yield
            yield from self.mandel_recursive(id, (Rect(x + half_x, y + half_y, half_x, half_y), canvas))
            if self.s1.task_time(id):
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
