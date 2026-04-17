import sys
import math
import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import colours, GuiManager, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle, Engine, StateManager

class Demo:
    # Coordinates around a cell, given as a delta table
    neighbours = ((-1, -1), (-1,  0), (-1, 1), (0, -1),
                  ( 0,  1), ( 1, -1), ( 1, 0), (1,  1))

    mandel_task_ids = ('iter', 'recu', '1', '2', '3', '4', 'can1', 'can2', 'can3', 'can4')

    cols = ((66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
            (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
            (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
            (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3))

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
        g1.set_screen_lifecycle(
            preamble=self.gui1_screen_preamble,
            event_handler=self.gui1_screen_event_handler,
            postamble=self.gui1_screen_postamble,
        )
        b1 = g1.bitmap_factory
        # blit a background image to the screen surface
        g1.set_pristine('backdrop.jpg')
        # screen label
        b1.set_font('gui_do')
        self.gui_do_label = g1.label((50, 30), 'gui_do', True)
        b1.set_font('normal')
        self.gui_do_pos_x = float(self.gui_do_label.draw_rect.x)
        self.gui_do_pos_y = float(self.gui_do_label.draw_rect.y)
        self.gui_do_speed = 250.0
        self.gui_do_angle = math.radians(35.0)
        self.gui_do_last_ms = pygame.time.get_ticks()
        # -----------------------

        widget_height = 28
        # exit button
        g1.button('exit', Rect(10, 1042, 70, widget_height), ButtonStyle.Angle, 'Exit')
        # setup for the togglebuttons
        g1.set_grid_properties((85, 1042), 120, widget_height, 4)
        # switch to gui2 button
        self.gui2_button = g1.button('gui2', g1.gridded(0, 0), ButtonStyle.Round, 'GUI 2')
        # control whether the background circles are drawn
        self.circles_toggle = g1.toggle('circles', g1.gridded(1, 0), ButtonStyle.Round, False, 'Circles')
        # control whether the buttons and toggles window is visible
        self.buttons_toggle = g1.toggle('Buttons_Window', g1.gridded(2, 0), ButtonStyle.Round, False, 'Buttons')
        # control whether the scrollbar window is visible
        self.scrollbars_toggle = g1.toggle('Scrollbar_Window', g1.gridded(3, 0), ButtonStyle.Round, False, 'Scrollbars')
        # control whether the life window is visible
        self.life_toggle = g1.toggle('life_Window', g1.gridded(4, 0), ButtonStyle.Round, False, 'Life')
        # control whether the Mandelbrot window is visible
        self.mandel_toggle = g1.toggle('mandel_Window', g1.gridded(5, 0), ButtonStyle.Round, False, 'Mandelbrot')
        # make the button groups, buttons, and toggles window
        x_pos, y_pos = 50, 150
        g1.set_grid_properties((10, 10), 120, widget_height, 2)
        self.button_group_win = g1.window('Button Groups, Buttons, and Toggles',
                                          (x_pos, y_pos), (g1.gridded(7, 0).right + 10, g1.gridded(0, 6).bottom),
                                          event_handler=self.buttons_window_event_handler,
                                          )
        g1.label(g1.gridded(0, 0), 'G1 Boxed', True)
        g1.label(g1.gridded(1, 0), 'G2 Rounded', True)
        g1.label(g1.gridded(2, 0), 'G3 Angled', True)
        g1.label(g1.gridded(3, 0), 'G4 Radioed', True)
        g1.label(g1.gridded(4, 0), 'G5 Checked', True)
        g1.label(g1.gridded(5, 0), 'G6 Mixed', True)
        g1.label(g1.gridded(6, 0), 'Buttons', True)
        g1.label(g1.gridded(7, 0), 'Toggles', True)
        lbg1 = g1.buttongroup('bg1', 'bg1b01', g1.gridded(0, 1), ButtonStyle.Box, 'Box 1')
        g1.buttongroup('bg1', 'bg1b02', g1.gridded(0, 2), ButtonStyle.Box, 'Box 2',)
        g1.buttongroup('bg1', 'bg1b03', g1.gridded(0, 3), ButtonStyle.Box, 'Box 3',)
        g1.buttongroup('bg1', 'bg1b04', g1.gridded(0, 4), ButtonStyle.Box, 'Box 4',)
        g1.buttongroup('bg1', 'bg1b05', g1.gridded(0, 5), ButtonStyle.Box, 'Box 5',)
        lbg2 = g1.buttongroup('bg2', 'bg2b01', g1.gridded(1, 1), ButtonStyle.Round, 'Round 1')
        g1.buttongroup('bg2', 'bg2b02', g1.gridded(1, 2), ButtonStyle.Round, 'Round 2')
        g1.buttongroup('bg2', 'bg2b03', g1.gridded(1, 3), ButtonStyle.Round, 'Round 3')
        g1.buttongroup('bg2', 'bg2b04', g1.gridded(1, 4), ButtonStyle.Round, 'Round 4')
        g1.buttongroup('bg2', 'bg2b05', g1.gridded(1, 5), ButtonStyle.Round, 'Round 5')
        lbg3 = g1.buttongroup('bg3', 'bg3b01', g1.gridded(2, 1), ButtonStyle.Angle, 'Angle 1')
        g1.buttongroup('bg3', 'bg3b02', g1.gridded(2, 2), ButtonStyle.Angle, 'Angle 2')
        g1.buttongroup('bg3', 'bg3b03', g1.gridded(2, 3), ButtonStyle.Angle, 'Angle 3')
        g1.buttongroup('bg3', 'bg3b04', g1.gridded(2, 4), ButtonStyle.Angle, 'Angle 4')
        g1.buttongroup('bg3', 'bg3b05', g1.gridded(2, 5), ButtonStyle.Angle, 'Angle 5')
        lbg4 = g1.buttongroup('bg4', 'bg4b01', g1.gridded(3, 1), ButtonStyle.Radio, 'Radio 1')
        g1.buttongroup('bg4', 'bg4b02', g1.gridded(3, 2), ButtonStyle.Radio, 'Radio 2')
        g1.buttongroup('bg4', 'bg4b03', g1.gridded(3, 3), ButtonStyle.Radio, 'Radio 3')
        g1.buttongroup('bg4', 'bg4b04', g1.gridded(3, 4), ButtonStyle.Radio, 'Radio 4')
        g1.buttongroup('bg4', 'bg4b05', g1.gridded(3, 5), ButtonStyle.Radio, 'Radio 5')
        lbg5 = g1.buttongroup('bg5', 'bg5b01', g1.gridded(4, 1), ButtonStyle.Check, 'Check 1')
        g1.buttongroup('bg5', 'bg5b02', g1.gridded(4, 2), ButtonStyle.Check, 'Check 2')
        g1.buttongroup('bg5', 'bg5b03', g1.gridded(4, 3), ButtonStyle.Check, 'Check 3')
        g1.buttongroup('bg5', 'bg5b04', g1.gridded(4, 4), ButtonStyle.Check, 'Check 4')
        g1.buttongroup('bg5', 'bg5b05', g1.gridded(4, 5), ButtonStyle.Check, 'Check 5')
        lbg6 = g1.buttongroup('bg6', 'bg6b01', g1.gridded(5, 1), ButtonStyle.Box, 'Mix 1')
        g1.buttongroup('bg6', 'bg6b02', g1.gridded(5, 2), ButtonStyle.Round, 'Mix 2')
        g1.buttongroup('bg6', 'bg6b03', g1.gridded(5, 3), ButtonStyle.Angle, 'Mix 3')
        g1.buttongroup('bg6', 'bg6b04', g1.gridded(5, 4), ButtonStyle.Radio, 'Mix 4')
        g1.buttongroup('bg6', 'bg6b05', g1.gridded(5, 5), ButtonStyle.Check, 'Mix 5')
        g1.button('b1', g1.gridded(6, 1), ButtonStyle.Box, 'Button 1')
        g1.button('b2', g1.gridded(6, 2), ButtonStyle.Round, 'Button 2')
        g1.button('b3', g1.gridded(6, 3), ButtonStyle.Angle, 'Button 3')
        g1.button('b4', g1.gridded(6, 4), ButtonStyle.Radio, 'Button 4')
        g1.button('b5', g1.gridded(6, 5), ButtonStyle.Check, 'Button 5')
        g1.toggle('t1', g1.gridded(7, 1), ButtonStyle.Box, False, 'Push 1', 'Raise 1')
        g1.toggle('t2', g1.gridded(7, 2), ButtonStyle.Round, False, 'Push 2', 'Raise 2')
        g1.toggle('t3', g1.gridded(7, 3), ButtonStyle.Angle, False, 'Push 3', 'Raise 3')
        g1.toggle('t4', g1.gridded(7, 4), ButtonStyle.Radio, False, 'Push 4', 'Raise 4')
        g1.toggle('t5', g1.gridded(7, 5), ButtonStyle.Check, False, 'Push 5', 'Raise 5')
        g1.set_grid_properties((10, g1.gridded(0, 5).bottom + 4), 122, widget_height, 0, False)
        self.label1 = g1.label(g1.gridded(0, 0), f'ID: {lbg1.read_id()}', True)
        self.label2 = g1.label(g1.gridded(1, 0), f'ID: {lbg2.read_id()}', True)
        self.label3 = g1.label(g1.gridded(2, 0), f'ID: {lbg3.read_id()}', True)
        self.label4 = g1.label(g1.gridded(3, 0), f'ID: {lbg4.read_id()}', True)
        self.label5 = g1.label(g1.gridded(4, 0), f'ID: {lbg5.read_id()}', True)
        self.label6 = g1.label(g1.gridded(5, 0), f'ID: {lbg6.read_id()}', True)
        # make the scrollbar window
        y_pos += 248
        self.scrollbar_win = g1.window(
            'Scrollbars',
            (x_pos, y_pos),
            (320, 362)
        )
        x = y = 10
        g1.scrollbar('Scrollbar_a', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Skip, (100, 0, 30, 10))
        y += 22
        g1.scrollbar('Scrollbar_b', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Split, (100, 0, 30, 10))
        y += 22
        g1.scrollbar('Scrollbar_c', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Near, (100, 0, 30, 10))
        y += 22
        g1.scrollbar('Scrollbar_d', Rect(x, y, 300, 20), Orientation.Horizontal, ArrowPosition.Far, (100, 0, 30, 10))
        y += 24
        g1.scrollbar('Scrollbar_e', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Skip, (100, 0, 30, 10))
        x += 22
        g1.scrollbar('Scrollbar_f', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Split, (100, 0, 30, 10))
        x += 22
        g1.scrollbar('Scrollbar_g', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Near, (100, 0, 30, 10))
        x += 22
        g1.scrollbar('Scrollbar_h', Rect(x, y, 20, 250), Orientation.Vertical, ArrowPosition.Far, (100, 0, 30, 10))
        g1.image('realize', Rect(x + 25, y, 210, 210), 'realize.png', False)
        b1.set_font('scroll')
        g1.label((x + 30, y + 215), 'Scrollbars!', True)
        b1.set_font('normal')
        # make the Conway's Game of Life window
        x_pos += 327
        width, height = 600, 600
        self.life_win = g1.window(
            'Conway\'s Game of Life',
            (x_pos, y_pos),
            (width, height),
            event_handler=self.life_window_event_handler,
            postamble=self.life_window_postamble
        )
        self.canvas = g1.canvas('life', Rect(10, 10, width - 20, height - (widget_height * 2)), on_activate=self.handle_Canvas, automatic_pristine=True)
        self.canvas.set_event_queue_limit(256)
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.draw_rect
        # a set to hold cell coordinates as tuples of x and y
        self.life = set()
        g1.set_grid_properties((10, height - widget_height - 10), 100, widget_height, 2)
        # resets the life simulation to a default state, uses a callback function
        g1.button('life_reset', g1.gridded(0, 0), ButtonStyle.Angle, 'Reset')
        # toggle whether or not the simulation is processing
        self.toggle_life = g1.toggle('run', g1.gridded(1, 0), ButtonStyle.Round, False, 'Stop', 'Start')
        width, height = 600, 600
        pos = x_pos + 607, y_pos
        mandel_overall = Rect(10, 10, width - 20, height - (widget_height * 2))
        self.mandel_win = g1.window(
            'Mandelbrot',
            pos,
            (width, height),
            event_handler=self.mandel_window_event_handler
        )
        g1.set_task_owners(self.mandel_win, *Demo.mandel_task_ids)
        self.mandel_canvas = g1.canvas('mandel', mandel_overall)
        g1.hide_widgets(self.mandel_canvas)
        self.mandel_canvas_rect = self.mandel_canvas.draw_rect
        cx, cy, cwidth, cheight = self.mandel_canvas.draw_rect
        chalfx, chalfy = (cwidth - 20) // 2, (cheight - 20) // 2
        self.canvas1 = g1.canvas('can1', Rect(10, 10, chalfx + 10, chalfy + 10))
        self.canvas2 = g1.canvas('can2', Rect(13 + chalfx + 5, 10, chalfx + 10, chalfy + 10))
        self.canvas3 = g1.canvas('can3', Rect(10, 13 + chalfy + 5, chalfx + 10, chalfy + 10))
        self.canvas4 = g1.canvas('can4', Rect(13 + chalfx + 5, 13 + chalfy + 5, chalfx + 10, chalfy + 10))
        g1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
        self.clear_mandel_surfaces()
        g1.set_grid_properties((10, height - widget_height - 10), int((600 - 30) / 5), widget_height, 2)
        g1.button('mandel_reset', g1.gridded(0, 0), ButtonStyle.Angle, 'Reset')
        g1.button('iterative', g1.gridded(1, 0), ButtonStyle.Round, 'Iterative')
        g1.button('recursive', g1.gridded(2, 0), ButtonStyle.Round, 'Recursive')
        g1.button('1split', g1.gridded(3, 0), ButtonStyle.Round, '1M 4 Tasks')
        g1.button('4split', g1.gridded(4, 0), ButtonStyle.Round, '4M 4 Tasks')
        # set cursor image
        g1.set_cursor((1, 1), 'cursor.png')
        self.gui1 = g1
        # -----------------------
        # begin gui2
        # -----------------------
        g2 = GuiManager(self.screen, fonts)
        g2.set_screen_lifecycle(
            preamble=self.gui2_screen_preamble,
            event_handler=self.gui2_screen_event_handler
        )
        g2.bitmap_factory.set_font('normal')
        g2.set_pristine('backdrop.jpg')
        g2.button('return', Rect(10, 1042, 70, widget_height), ButtonStyle.Angle, 'Back')
        g2.window(
            'GUI 2',
            (50, 150),
            (300, 300)
        )
        # set cursor for gui2
        g2.set_cursor((1, 1), 'cursor.png')
        self.gui2 = g2
        # -----------------------
        # Setup Engine and StateManager
        # -----------------------
        self.state_manager = StateManager()
        # Register contexts with StateManager
        self.state_manager.register_context('gui1', self.gui1)
        self.state_manager.register_context('gui2', self.gui2)
        # references to the schedulers
        self.s1 = self.gui1.scheduler
        self.s2 = self.gui2.scheduler
        # Keep per-frame callback work bounded so bursty task progress updates do not hitch rendering.
        self.s1.set_message_dispatch_limit(256)
        self.s2.set_message_dispatch_limit(256)
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
        self._life_canvas_last_drop_count = 0
        self.canvas.set_overflow_handler(self._handle_life_canvas_overflow)
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
        self.engine.run()

    def _update_gui1_window_visibility(self):
        self.button_group_win.visible = self.buttons_toggle.pushed
        self.scrollbar_win.visible = self.scrollbars_toggle.pushed
        self.life_win.visible = self.life_toggle.pushed
        self.mandel_win.visible = self.mandel_toggle.pushed

    def gui1_screen_preamble(self):
        self.gui1.restore_pristine()
        if not self.dragging and self.gui1.locking_object is self.canvas:
            self.gui1.set_lock_point(None)
        if self.circles_toggle.pushed:
            self.update_circles(self.size)
        self._update_gui1_window_visibility()

    def gui1_screen_event_handler(self, event):
        if event.type == Event.Widget:
            if event.widget_id == 'exit':
                self.state_manager.set_running(False)
            elif event.widget_id == 'gui2':
                self.state_manager.switch_context('gui2')
        elif event.type == Event.KeyDown:
            if event.key == K_ESCAPE:
                self.state_manager.set_running(False)
        elif event.type == Event.Quit:
            self.state_manager.set_running(False)

    def gui1_screen_postamble(self):
        self.update_gui_do_label()

    def update_gui_do_label(self):
        now_ms = pygame.time.get_ticks()
        dt = (now_ms - self.gui_do_last_ms) / 1000.0
        self.gui_do_last_ms = now_ms
        if dt < 0.0:
            dt = 0.0
        elif dt > 0.05:
            dt = 0.05
        distance = self.gui_do_speed * dt
        self.gui_do_pos_x += math.cos(self.gui_do_angle) * distance
        self.gui_do_pos_y += math.sin(self.gui_do_angle) * distance
        x = self.gui_do_pos_x
        y = self.gui_do_pos_y
        max_x = self.screen_rect.width - self.gui_do_label.draw_rect.width
        max_y = self.screen_rect.height - self.gui_do_label.draw_rect.height
        hit_vertical = False
        hit_horizontal = False
        if x < 0:
            x = 0
            hit_vertical = True
        elif x > max_x:
            x = max_x
            hit_vertical = True
        if y < 0:
            y = 0
            hit_horizontal = True
        elif y > max_y:
            y = max_y
            hit_horizontal = True
        if hit_vertical:
            self.gui_do_angle = math.pi - self.gui_do_angle
        if hit_horizontal:
            self.gui_do_angle = -self.gui_do_angle
        self.gui_do_angle %= (2.0 * math.pi)
        self.gui_do_pos_x = x
        self.gui_do_pos_y = y
        self.gui_do_label.set_pos((int(round(x)), int(round(y))))

    def buttons_window_event_handler(self, event):
        if event.type != Event.Group:
            return
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

    def life_window_event_handler(self, event):
        if event.type == Event.Widget and event.widget_id == 'life_reset':
            self.life_reset()

    def life_window_postamble(self):
        if self.toggle_life.pushed:
            self.generate()
        self.draw_life()

    def mandel_window_event_handler(self, event):
        if event.type == Event.Task:
            self.handle_mandel_task_event(event)
            return
        if event.type != Event.Widget:
            return
        if event.widget_id == 'mandel_reset':
            self.s1.remove_tasks(*Demo.mandel_task_ids)
            self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
            self.gui1.show_widgets(self.mandel_canvas)
            self.clear_mandel_surfaces()
            return
        if self.s1.tasks_busy_match_any(*Demo.mandel_task_ids):
            return
        if event.widget_id == 'iterative':
            self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
            self.gui1.show_widgets(self.mandel_canvas)
            self.clear_mandel_surfaces()
            _, _, w, h = self.mandel_canvas_rect
            self.mandel_setup(w, h)
            self.s1.add_task('iter', self.mandel_iterative, message_method=self.make_mandel_progress_handler('iter'))
        elif event.widget_id == 'recursive':
            self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
            self.gui1.show_widgets(self.mandel_canvas)
            self.clear_mandel_surfaces()
            _, _, w, h = self.mandel_canvas_rect
            self.mandel_setup(w, h)
            self.s1.add_task('recu', self.mandel_recursive, Rect(0, 0, w, h),
                             message_method=self.make_mandel_progress_handler('recu'))
        elif event.widget_id == '1split':
            self.gui1.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
            self.gui1.show_widgets(self.mandel_canvas)
            self.clear_mandel_surfaces()
            _, _, w, h = self.mandel_canvas_rect
            self.mandel_setup(w, h)
            left_w, top_h = w // 2, h // 2
            right_w, bottom_h = w - left_w, h - top_h
            self.s1.add_task('1', self.mandel_recursive, Rect(0, 0, left_w, top_h),
                             message_method=self.make_mandel_progress_handler('1'))
            self.s1.add_task('2', self.mandel_recursive, Rect(left_w, 0, right_w, top_h),
                             message_method=self.make_mandel_progress_handler('2'))
            self.s1.add_task('3', self.mandel_recursive, Rect(0, top_h, left_w, bottom_h),
                             message_method=self.make_mandel_progress_handler('3'))
            self.s1.add_task('4', self.mandel_recursive, Rect(left_w, top_h, right_w, bottom_h),
                             message_method=self.make_mandel_progress_handler('4'))
        elif event.widget_id == '4split':
            self.gui1.hide_widgets(self.mandel_canvas)
            self.gui1.show_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
            self.clear_mandel_surfaces()
            _, _, w1, h1 = self.mandel_canvas.draw_rect
            w1 = w1 // 2
            h1 = h1 // 2
            self.mandel_setup(w1, h1)
            self.s1.add_task('can1', self.mandel_recursive, Rect(0, 0, w1, h1),
                             message_method=self.make_mandel_progress_handler('can1'))
            self.s1.add_task('can2', self.mandel_recursive, Rect(0, 0, w1, h1),
                             message_method=self.make_mandel_progress_handler('can2'))
            self.s1.add_task('can3', self.mandel_recursive, Rect(0, 0, w1, h1),
                             message_method=self.make_mandel_progress_handler('can3'))
            self.s1.add_task('can4', self.mandel_recursive, Rect(0, 0, w1, h1),
                             message_method=self.make_mandel_progress_handler('can4'))

    def handle_mandel_task_event(self, event):
        task_id = getattr(event, 'id', None)
        if task_id is None:
            return
        if getattr(event, 'error', None):
            print(f'Task failed: id={task_id} error={event.error}', file=sys.stderr)
            return
        if task_id in Demo.mandel_task_ids:
            self.s1.pop_result(task_id)

    def gui2_screen_preamble(self):
        self.gui2.restore_pristine()

    def gui2_screen_event_handler(self, event):
        if event.type == Event.Widget:
            if event.widget_id == 'return':
                self.state_manager.switch_context('gui1')
        elif event.type == Event.Task:
            if getattr(event, 'error', None):
                print(f'Task failed: id={getattr(event, "id", None)} error={event.error}', file=sys.stderr)
        elif event.type == Event.KeyDown:
            if event.key == K_ESCAPE:
                self.state_manager.set_running(False)
        elif event.type == Event.Quit:
            self.state_manager.set_running(False)

    # Canvas callback function
    def _handle_life_canvas_overflow(self, _dropped: int, total_dropped: int) -> None:
        # Throttle logging so sustained pressure does not flood stderr.
        if total_dropped == 1 or (total_dropped - self._life_canvas_last_drop_count) >= 16:
            delta = total_dropped - self._life_canvas_last_drop_count
            self._life_canvas_last_drop_count = total_dropped
            print(f'Canvas event overflow: dropped {delta} events (total={total_dropped})', file=sys.stderr)

    def handle_Canvas(self):
        # read the event from the canvas widget
        CEvent = self.canvas.read_event()
        if CEvent is not None:
            # parse that event by kind and parameters
            if CEvent.type == CanvasEvent.MouseButtonDown:
                # right-mouse button pressed, enter dragging state
                if CEvent.button == 3:
                    self.dragging = True
                    self.gui1.set_lock_point(self.canvas)
            elif CEvent.type == CanvasEvent.MouseButtonUp:
                # right-mouse button released, exit dragging state
                if CEvent.button == 3:
                    self.dragging = False
                    self.gui1.set_lock_point(None)
            elif CEvent.type == CanvasEvent.MouseMotion:
                # if dragging then track relative position
                if self.dragging and CEvent.rel is not None:
                    x, y = CEvent.rel[0], CEvent.rel[1]
                    self.origin_x += x
                    self.origin_y += y
            elif CEvent.type == CanvasEvent.MouseWheel:
                # handle the mouse wheel
                if CEvent.y is not None:
                    old_size = self.cell_size
                    new_size = old_size + (CEvent.y * 2)
                    if new_size < 6:
                        new_size = 6
                    elif new_size > 24:
                        new_size = 24
                    if new_size != old_size:
                        mouse_x, mouse_y = (CEvent.pos if CEvent.pos is not None else self.canvas_rect.center)
                        # Keep the world position under the mouse fixed while scaling.
                        self.origin_x = mouse_x - ((mouse_x - self.origin_x) / old_size) * new_size
                        self.origin_y = mouse_y - ((mouse_y - self.origin_y) / old_size) * new_size
                        self.cell_size = new_size

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
        self.toggle_life.pushed = False
        # the starting configuration of the Life grid
        self.life = set({(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)})

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
        rect = Rect(0, 0, self.mandel_width, self.mandel_height)
        self._compute_iterative_region(id, rect)
        return None

    def mandel_recursive(self, id, item):
        x, y, w, h = item
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.mandel_width, x + w)
        y1 = min(self.mandel_height, y + h)
        if x1 <= x0 or y1 <= y0:
            return None
        x, y, w, h = x0, y0, x1 - x0, y1 - y0

        def fill_region(x_pos, y_pos, width, height, value):
            # Send a compact fill payload so the GUI thread can draw this block with one fill call.
            self.s1.send_message(id, (x_pos, y_pos, width, height, value))

        def publish_pixel_block(x_pos, y_pos, width, height, block_values):
            self.s1.send_message(id, (x_pos, y_pos, width, height, block_values))

        def recursive_region(x_pos, y_pos, width, height):
            if width <= 0 or height <= 0:
                return
            top_left = self.pixel(x_pos, y_pos)
            accuracy = 2
            not_hit = True
            for x_test in range(0, width, accuracy):
                if (self.pixel(x_pos + x_test, y_pos) != top_left) or (self.pixel(x_pos + x_test, y_pos + height - 1) != top_left):
                    not_hit = False
                    break
            if not_hit:
                for y_test in range(0, height, accuracy):
                    if (self.pixel(x_pos, y_pos + y_test) != top_left) or (self.pixel(x_pos + width - 1, y_pos + y_test) != top_left):
                        not_hit = False
                        break
            if not_hit:
                fill_region(x_pos, y_pos, width, height, top_left)
                return
            if width > 2 or height > 2:
                half_x = (width + (width % 2)) // 2
                half_y = (height + (height % 2)) // 2
                recursive_region(x_pos, y_pos, half_x, half_y)
                recursive_region(x_pos + half_x, y_pos, width - half_x, half_y)
                recursive_region(x_pos + half_x, y_pos + half_y, width - half_x, height - half_y)
                recursive_region(x_pos, y_pos + half_y, half_x, height - half_y)
                return
            right = x_pos + width - 1
            bottom = y_pos + height - 1
            top_right = self.pixel(right, y_pos)
            bottom_left = self.pixel(x_pos, bottom)
            bottom_right = self.pixel(right, bottom)
            block_values = [top_left]
            if width > 1:
                block_values.append(top_right)
            if height > 1:
                block_values.append(bottom_left)
            if width > 1 and height > 1:
                block_values.append(bottom_right)
            publish_pixel_block(x_pos, y_pos, width, height, block_values)
        recursive_region(x, y, w, h)
        return None

    def _compute_iterative_region(self, task_id, rect):
        x, y, w, h = rect
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.mandel_width, x + w)
        y1 = min(self.mandel_height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        x, y, w, h = x0, y0, x1 - x0, y1 - y0

        chunk_rows = 4
        row_values = []
        chunk_start_y = y
        for y_pos in range(y, y + h):
            for x_pos in range(x, x + w):
                row_values.append(self.pixel(x_pos, y_pos))
            rows_in_chunk = ((y_pos - chunk_start_y) + 1)
            if rows_in_chunk >= chunk_rows:
                self.s1.send_message(task_id, (x, chunk_start_y, w, rows_in_chunk, row_values))
                chunk_start_y = y_pos + 1
                row_values = []
        if row_values:
            rows_in_chunk = y + h - chunk_start_y
            self.s1.send_message(task_id, (x, chunk_start_y, w, rows_in_chunk, row_values))

    def make_mandel_progress_handler(self, task_id):
        def handler(result):
            self.apply_mandel_result(task_id, result)
        return handler

    def apply_mandel_result(self, task_id, result):
        x, y, w, h, values = result
        if task_id in {'iter', 'recu', '1', '2', '3', '4'}:
            canvas = self.mandel_canvas.canvas
        elif task_id == 'can1':
            canvas = self.canvas1.canvas
        elif task_id == 'can2':
            canvas = self.canvas2.canvas
        elif task_id == 'can3':
            canvas = self.canvas3.canvas
        elif task_id == 'can4':
            canvas = self.canvas4.canvas
        else:
            return

        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(canvas.get_width(), x + w)
        y1 = min(canvas.get_height(), y + h)
        if x1 <= x0 or y1 <= y0:
            return

        if (x0, y0, x1, y1) != (x, y, x + w, y + h):
            if isinstance(values, int):
                canvas.fill(self.col(values), Rect(x0, y0, x1 - x0, y1 - y0))
                return
            src_w = w
            clipped_values = []
            for row in range(y0 - y, y1 - y):
                start = row * src_w + (x0 - x)
                end = start + (x1 - x0)
                clipped_values.extend(values[start:end])
            values = clipped_values
            x, y, w, h = x0, y0, x1 - x0, y1 - y0

        if isinstance(values, int):
            canvas.fill(self.col(values), Rect(x, y, w, h))
            return
        idx = 0
        canvas.lock()
        try:
            for y_pos in range(y, y + h):
                for x_pos in range(x, x + w):
                    canvas.set_at((x_pos, y_pos), self.col(values[idx]))
                    idx += 1
        finally:
            canvas.unlock()

    def pixel(self, x, y):
        c = self.center + (x - self.mandel_width // 2 + (y - self.mandel_height // 2) * 1j) * self.scale
        z = 0
        for k in range(self.max_iter):
            z = z ** 2 + c
            if (z * z.conjugate()).real > 4.0:
                break
        return k

    def col(self, k):
        if k == self.maximum_iters:
            return (0, 0, 0)
        else:
            return Demo.cols[k % 16]

if __name__ == '__main__':
    Demo().run()
