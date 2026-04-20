import sys
import math
import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import colours, GuiManager, Event, CanvasEvent, Orientation, ArrowPosition, ButtonStyle, Engine, StateManager

class Demo:
    # Coordinates around a cell, given as a delta table for Conway's Game of Life
    neighbours = ((-1, -1), (-1,  0), (-1, 1), (0, -1),
                  ( 0,  1), ( 1, -1), ( 1, 0), (1,  1))

    # id's for the task scheduler the mandelbrot uses
    mandel_task_ids = ('iter', 'recu', '1', '2', '3', '4', 'can1', 'can2', 'can3', 'can4')

    # a tuple of colours as (R, G, B) the mandelbrot uses
    cols = ((66, 30, 15), (25, 7, 26), (9, 1, 47), (4, 4, 73),
            (0, 7, 100), (12, 44, 138), (24, 82, 177), (57, 125, 209),
            (134, 181, 229), (211, 236, 248), (241, 233, 191), (248, 201, 95),
            (255, 170, 0), (204, 128, 0), (153, 87, 0), (106, 52, 3))

    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # save screen rect
        self.screen_rect = self.screen.get_rect()
        # set window caption
        pygame.display.set_caption('Demo')
        # -----------------------
        # begin gui1
        # -----------------------
        # create a gui manager
        g1 = GuiManager(self.screen)
        g1.configure_fonts(
            titlebar=('Ubuntu-B.ttf', 14),
            normal=('Gimbot.ttf', 16),
            gui_do=('Gimbot.ttf', 72),
        )
        g1.configure_task_panel(event_handler=self.gui1_panel_event_handler)
        g1.set_screen_lifecycle(
            preamble=self.gui1_screen_preamble,
            event_handler=self.gui1_panel_event_handler,
            postamble=self.gui1_screen_postamble,
        )
        b1 = g1.graphics_factory
        b1.register_cursor(name='normal', filename='cursor.png', hotspot=(1, 1))
        b1.register_cursor(name='hand', filename='hand.png', hotspot=(12, 12))
        # load an image that will be used for a backdrop, display it on-screen and save it for restore_pristine
        g1.set_pristine('backdrop.jpg')
        # screen label
        b1.set_font('gui_do')
        self.gui_do_label = g1.label((50, 30), 'gui_do', True)
        b1.set_font('normal')
        # variables for moving the label around the screen
        self.gui_do_pos_x = float(self.gui_do_label.draw_rect.x)
        self.gui_do_pos_y = float(self.gui_do_label.draw_rect.y)
        self.gui_do_speed = 250.0
        self.gui_do_angle = math.radians(35.0)
        self.gui_do_last_ms = pygame.time.get_ticks()
        # general widget height
        widget_height = 28
        # -----------------------
        # widgets in a bottom task panel
        # -----------------------
        g1.begin_task_panel()
        # exit button
        g1.button('exit', Rect(10, 5, 70, widget_height), ButtonStyle.Angle, 'Exit')
        # setup for the togglebuttons
        g1.set_grid_properties((85, 5), 120, widget_height, 4)
        # switch to gui2 button
        self.gui2_button = g1.button('gui2', g1.gridded(0, 0), ButtonStyle.Round, 'Apps')
        # control whether the background circles are drawn
        self.circles_toggle = g1.toggle('circles', g1.gridded(1, 0), ButtonStyle.Round, False, 'Drawing')
        # control whether the buttons and toggles window is visible
        self.buttons_toggle = g1.toggle('Buttons_Window', g1.gridded(2, 0), ButtonStyle.Round, False, 'Styles')
        g1.end_task_panel()
        # -----------------------
        # screen widget layout demos (enabled and disabled)
        # -----------------------
        top_section_x = 70
        top_section_y = 70
        half_height = self.screen_rect.height // 2
        bottom_section_y = half_height + 30
        self._slider_label_centers = {}
        self._create_gui1_screen_widgets_layout(g1, top_section_x, top_section_y)
        self._create_gui1_screen_widgets_layout(g1, top_section_x, bottom_section_y, disabled=True)
        # -----------------------
        # make the button groups, buttons, and toggles window
        # -----------------------
        g1.set_grid_properties((10, 10), 120, widget_height, 2)
        button_group_window_size = (g1.gridded(7, 0).right + 10, g1.gridded(0, 6).bottom)
        x_pos = (self.screen_rect.width - button_group_window_size[0]) // 2
        y_pos = (self.screen_rect.height - button_group_window_size[1]) // 2
        self.button_group_win = g1.window('Button Groups, Buttons, and Toggles',
                          (x_pos, y_pos), button_group_window_size,
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
        lbg1 = g1.button_group('bg1', 'bg1b01', g1.gridded(0, 1), ButtonStyle.Box, 'Box 1')
        g1.button_group('bg1', 'bg1b02', g1.gridded(0, 2), ButtonStyle.Box, 'Box 2',)
        g1.button_group('bg1', 'bg1b03', g1.gridded(0, 3), ButtonStyle.Box, 'Box 3',)
        g1.button_group('bg1', 'bg1b04', g1.gridded(0, 4), ButtonStyle.Box, 'Box 4',)
        g1.button_group('bg1', 'bg1b05', g1.gridded(0, 5), ButtonStyle.Box, 'Box 5',)
        lbg2 = g1.button_group('bg2', 'bg2b01', g1.gridded(1, 1), ButtonStyle.Round, 'Round 1')
        g1.button_group('bg2', 'bg2b02', g1.gridded(1, 2), ButtonStyle.Round, 'Round 2')
        g1.button_group('bg2', 'bg2b03', g1.gridded(1, 3), ButtonStyle.Round, 'Round 3')
        g1.button_group('bg2', 'bg2b04', g1.gridded(1, 4), ButtonStyle.Round, 'Round 4')
        g1.button_group('bg2', 'bg2b05', g1.gridded(1, 5), ButtonStyle.Round, 'Round 5')
        lbg3 = g1.button_group('bg3', 'bg3b01', g1.gridded(2, 1), ButtonStyle.Angle, 'Angle 1')
        g1.button_group('bg3', 'bg3b02', g1.gridded(2, 2), ButtonStyle.Angle, 'Angle 2')
        g1.button_group('bg3', 'bg3b03', g1.gridded(2, 3), ButtonStyle.Angle, 'Angle 3')
        g1.button_group('bg3', 'bg3b04', g1.gridded(2, 4), ButtonStyle.Angle, 'Angle 4')
        g1.button_group('bg3', 'bg3b05', g1.gridded(2, 5), ButtonStyle.Angle, 'Angle 5')
        lbg4 = g1.button_group('bg4', 'bg4b01', g1.gridded(3, 1), ButtonStyle.Radio, 'Radio 1')
        g1.button_group('bg4', 'bg4b02', g1.gridded(3, 2), ButtonStyle.Radio, 'Radio 2')
        g1.button_group('bg4', 'bg4b03', g1.gridded(3, 3), ButtonStyle.Radio, 'Radio 3')
        g1.button_group('bg4', 'bg4b04', g1.gridded(3, 4), ButtonStyle.Radio, 'Radio 4')
        g1.button_group('bg4', 'bg4b05', g1.gridded(3, 5), ButtonStyle.Radio, 'Radio 5')
        lbg5 = g1.button_group('bg5', 'bg5b01', g1.gridded(4, 1), ButtonStyle.Check, 'Check 1')
        g1.button_group('bg5', 'bg5b02', g1.gridded(4, 2), ButtonStyle.Check, 'Check 2')
        g1.button_group('bg5', 'bg5b03', g1.gridded(4, 3), ButtonStyle.Check, 'Check 3')
        g1.button_group('bg5', 'bg5b04', g1.gridded(4, 4), ButtonStyle.Check, 'Check 4')
        g1.button_group('bg5', 'bg5b05', g1.gridded(4, 5), ButtonStyle.Check, 'Check 5')
        lbg6 = g1.button_group('bg6', 'bg6b01', g1.gridded(5, 1), ButtonStyle.Box, 'Mix 1')
        g1.button_group('bg6', 'bg6b02', g1.gridded(5, 2), ButtonStyle.Round, 'Mix 2')
        g1.button_group('bg6', 'bg6b03', g1.gridded(5, 3), ButtonStyle.Angle, 'Mix 3')
        g1.button_group('bg6', 'bg6b04', g1.gridded(5, 4), ButtonStyle.Radio, 'Mix 4')
        g1.button_group('bg6', 'bg6b05', g1.gridded(5, 5), ButtonStyle.Check, 'Mix 5')
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
        self.label1 = g1.label(g1.gridded(0, 0), f'ID: {lbg1.button_id}', True)
        self.label2 = g1.label(g1.gridded(1, 0), f'ID: {lbg2.button_id}', True)
        self.label3 = g1.label(g1.gridded(2, 0), f'ID: {lbg3.button_id}', True)
        self.label4 = g1.label(g1.gridded(3, 0), f'ID: {lbg4.button_id}', True)
        self.label5 = g1.label(g1.gridded(4, 0), f'ID: {lbg5.button_id}', True)
        self.label6 = g1.label(g1.gridded(5, 0), f'ID: {lbg6.button_id}', True)
        self._remember_slider_label_center(self.label1, self.label1.draw_rect.center)
        self._remember_slider_label_center(self.label2, self.label2.draw_rect.center)
        self._remember_slider_label_center(self.label3, self.label3.draw_rect.center)
        self._remember_slider_label_center(self.label4, self.label4.draw_rect.center)
        self._remember_slider_label_center(self.label5, self.label5.draw_rect.center)
        self._remember_slider_label_center(self.label6, self.label6.draw_rect.center)
        # set cursor image
        g1.set_cursor('normal')
        self.gui1 = g1
        # -----------------------
        # begin gui2
        # -----------------------
        g2 = GuiManager(self.screen)
        g2.configure_fonts(
            titlebar=('Ubuntu-B.ttf', 14),
            normal=('Gimbot.ttf', 16),
        )
        g2.configure_task_panel(event_handler=self.gui2_panel_event_handler)
        g2.set_screen_lifecycle(
            preamble=self.gui2_screen_preamble,
            event_handler=self.gui2_panel_event_handler
        )
        g2.graphics_factory.set_font('normal')
        g2.set_pristine('backdrop.jpg')
        g2.begin_task_panel()
        g2.button('back', Rect(10, 5, 70, widget_height), ButtonStyle.Angle, 'Back')
        g2.set_grid_properties((85, 5), 138, widget_height, 6)
        self.gui2_life_window_toggle = g2.toggle('gui2_life_window', g2.gridded(0, 0), ButtonStyle.Round, False, 'Life')
        self.gui2_mandel_window_toggle = g2.toggle('gui2_mandel_window', g2.gridded(1, 0), ButtonStyle.Round, False, 'Mandelbrot')
        g2.end_task_panel()

        # -----------------------
        # make the Conway's Game of Life window (gui2)
        # -----------------------
        width, height = 600, 600
        self.life_win = g2.window(
            'Conway\'s Game of Life',
            (0, 0),
            (width, height),
            preamble=self.life_window_preamble,
            event_handler=self.life_window_event_handler,
            postamble=self.life_window_postamble
        )
        self.canvas = g2.canvas('life', Rect(10, 10, width - 20, height - (widget_height * 2)), on_activate=self.handle_Canvas, automatic_pristine=True)
        self.canvas.set_event_queue_limit(256)
        self.canvas.set_overflow_handler(self.handle_canvas_overflow)
        self.canvas_surface = self.canvas.get_canvas_surface()
        self.canvas_rect = self.canvas.draw_rect
        # a set to hold cell coordinates as tuples of x and y
        self.life = set()
        g2.set_grid_properties((10, height - widget_height - 10), 100, widget_height, 2)
        # resets the life simulation to a default state, uses a callback function
        g2.button('life_reset', g2.gridded(0, 0), ButtonStyle.Angle, 'Reset')
        # toggle whether or not the simulation is processing
        self.toggle_life = g2.toggle('run', g2.gridded(1, 0), ButtonStyle.Round, False, 'Stop', 'Start')
        b2 = g2.graphics_factory
        zoom_label_bitmap = b2.render_text('Zoom', colours['text'], True)
        zoom_label_padding = 8
        slider_padding = 12
        slider_y = height - widget_height - 10
        zoom_label_x = self.canvas_rect.right - zoom_label_bitmap.get_width()
        slider_left = self.toggle_life.draw_rect.right + slider_padding
        slider_right = zoom_label_x - zoom_label_padding
        self.life_zoom_slider = g2.slider(
            'life_zoom_slider',
            Rect(slider_left, slider_y, max(80, slider_right - slider_left), widget_height),
            Orientation.Horizontal,
            11,
            0,
            True,
        )
        self._life_zoom_slider_last_value = int(self.life_zoom_slider.value)
        g2.label((zoom_label_x, slider_y + 6), 'Zoom', True)

        # -----------------------
        # make the mandelbrot window (gui2)
        # -----------------------
        width, height = 600, 600
        mandel_overall = Rect(10, 10, width - 20, height - (widget_height * 2))
        self.mandel_win = g2.window(
            'Mandelbrot',
            (0, 0),
            (width, height),
            event_handler=self.mandel_window_event_handler
        )
        g2.set_task_owners(self.mandel_win, *Demo.mandel_task_ids)
        self.mandel_canvas = g2.canvas('mandel', mandel_overall)
        g2.hide_widgets(self.mandel_canvas)
        self.mandel_canvas_rect = self.mandel_canvas.draw_rect
        _, _, cwidth, cheight = self.mandel_canvas.draw_rect
        chalfx, chalfy = (cwidth - 20) // 2, (cheight - 20) // 2
        self.canvas1 = g2.canvas('can1', Rect(10, 10, chalfx + 10, chalfy + 10))
        self.canvas2 = g2.canvas('can2', Rect(13 + chalfx + 5, 10, chalfx + 10, chalfy + 10))
        self.canvas3 = g2.canvas('can3', Rect(10, 13 + chalfy + 5, chalfx + 10, chalfy + 10))
        self.canvas4 = g2.canvas('can4', Rect(13 + chalfx + 5, 13 + chalfy + 5, chalfx + 10, chalfy + 10))
        g2.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
        self.clear_mandel_surfaces()
        g2.set_grid_properties((10, height - widget_height - 10), int((600 - 30) / 5), widget_height, 2)
        g2.button('mandel_reset', g2.gridded(0, 0), ButtonStyle.Angle, 'Reset')
        self.mandel_iterative_button = g2.button('iterative', g2.gridded(1, 0), ButtonStyle.Round, 'Iterative')
        self.mandel_recursive_button = g2.button('recursive', g2.gridded(2, 0), ButtonStyle.Round, 'Recursive')
        self.mandel_one_split_button = g2.button('1split', g2.gridded(3, 0), ButtonStyle.Round, '1M 4 Tasks')
        self.mandel_four_split_button = g2.button('4split', g2.gridded(4, 0), ButtonStyle.Round, '4M 4 Tasks')
        self.mandel_task_buttons = (
            self.mandel_iterative_button,
            self.mandel_recursive_button,
            self.mandel_one_split_button,
            self.mandel_four_split_button,
        )
        self.set_mandel_task_buttons_disabled(False)
        self.life_win.visible = False
        self.mandel_win.visible = False
        self._layout_gui2_sim_windows()
        # set cursor for gui2
        g2.set_cursor('normal')
        self.gui2 = g2
        # -----------------------
        # Setup Engine and StateManager
        # -----------------------
        self.state_manager = StateManager()
        # Register contexts with StateManager
        self.state_manager.register_context('gui1', self.gui1)
        self.state_manager.register_context('gui2', self.gui2)
        # reference to gui2 scheduler
        self.s2 = self.gui2.scheduler
        # Keep per-frame callback work bounded so bursty task progress updates do not hitch rendering.
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
        self.canvas.set_overflow_mode('drop_oldest')
        self.canvas.set_overflow_handler(self.handle_canvas_overflow)
        # number of circles
        circles = 64
        # size of circles
        self.size = 12
        # circle positions
        self.positions = []
        # make bitmaps for circles
        factory = g1.graphics_factory
        circle_bitmap_a = factory.draw_radio_bitmap(self.size, colours['light'], colours['none'])
        circle_bitmap_b = factory.draw_radio_bitmap(self.size, colours['medium'], colours['none'])
        # make position list for circles
        for _ in range(circles):
            x = randrange(self.size, self.screen_rect.width - (self.size * 2))
            y = randrange(self.size, self.screen_rect.height - (self.size * 2))
            dx = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            dy = choice([-randrange(2, self.size - 2), randrange(2, self.size - 2)])
            self.positions.append((x, y, dx, dy, choice([circle_bitmap_a, circle_bitmap_b])))

    # preambles, event handlers, and postambles in window definition order
    def gui1_screen_preamble(self):
        self.gui1.restore_pristine()
        if self.circles_toggle.pushed:
            self.update_circles(self.size)
        self._update_gui1_window_visibility()

    def gui1_panel_event_handler(self, event):
        if event.type == Event.Widget:
            if event.widget_id == 'exit':
                self.state_manager.set_running(False)
            elif event.widget_id == 'gui2':
                self.state_manager.switch_context('gui2')
            return
        self._handle_common_exit_events(event)

    def gui1_screen_postamble(self):
        self.update_slider_labels()
        self.update_gui_do_label()

    def buttons_window_event_handler(self, event):
        if event.type != Event.Group:
            return
        label_by_group = {
            'bg1': self.label1,
            'bg2': self.label2,
            'bg3': self.label3,
            'bg4': self.label4,
            'bg5': self.label5,
            'bg6': self.label6,
        }
        label = label_by_group.get(event.group)
        if label is not None:
            label.set_label(f'ID: {event.widget_id}')
            self._center_slider_label(label)

    def life_window_preamble(self):
        slider_value = int(self.life_zoom_slider.value)
        if slider_value == self._life_zoom_slider_last_value:
            return
        self._life_zoom_slider_last_value = slider_value
        old_size = self.cell_size
        if old_size <= 0:
            return
        zoom_value = max(1, min(12, slider_value + 1))
        new_size = zoom_value * 2
        if new_size == old_size:
            return
        center_x, center_y = self.canvas_rect.center
        self.origin_x = center_x - ((center_x - self.origin_x) / old_size) * new_size
        self.origin_y = center_y - ((center_y - self.origin_y) / old_size) * new_size
        self.cell_size = new_size

    def life_window_event_handler(self, event):
        if event.type == Event.Widget and event.widget_id == 'life_reset':
            self.life_reset()

    def life_window_postamble(self):
        if self.toggle_life.pushed:
            self.generate()
        self.draw_life()

    def mandel_window_event_handler(self, event):
        # Task events carry async worker progress/completion payloads.
        if event.type == Event.Task:
            self.handle_mandel_task_event(event)
            return
        if event.type != Event.Widget:
            return
        widget_id = event.widget_id
        if widget_id == 'mandel_reset':
            self.s2.remove_tasks(*Demo.mandel_task_ids)
            self._show_single_mandel_canvas()
            self.set_mandel_task_buttons_disabled(False)
            return
        if self.s2.tasks_busy_match_any(*Demo.mandel_task_ids):
            # Ignore new launch requests while any Mandelbrot job is running.
            return
        if widget_id == 'iterative':
            # One full-canvas task using scanline iteration.
            self._prepare_mandel_single_canvas_run()
            _, _, w, h = self.mandel_canvas_rect
            self.mandel_setup(w, h)
            self.s2.add_task('iter', self.mandel_iterative, message_method=self.make_mandel_progress_handler('iter'))
        elif widget_id == 'recursive':
            # One full-canvas task using adaptive recursive subdivision.
            self._prepare_mandel_single_canvas_run()
            _, _, w, h = self.mandel_canvas_rect
            self.mandel_setup(w, h)
            self._queue_mandel_recursive_task('recu', Rect(0, 0, w, h))
        elif widget_id == '1split':
            # Four quadrant tasks that render into one shared Mandelbrot canvas.
            self._prepare_mandel_single_canvas_run()
            _, _, w, h = self.mandel_canvas_rect
            self.mandel_setup(w, h)
            left_w, top_h = w // 2, h // 2
            right_w, bottom_h = w - left_w, h - top_h
            self._queue_mandel_recursive_task('1', Rect(0, 0, left_w, top_h))
            self._queue_mandel_recursive_task('2', Rect(left_w, 0, right_w, top_h))
            self._queue_mandel_recursive_task('3', Rect(0, top_h, left_w, bottom_h))
            self._queue_mandel_recursive_task('4', Rect(left_w, top_h, right_w, bottom_h))
        elif widget_id == '4split':
            # Four independent canvases, each rendering its own quadrant-sized image.
            self._prepare_mandel_split_canvas_run()
            _, _, w1, h1 = self.mandel_canvas_rect
            w1 = w1 // 2
            h1 = h1 // 2
            self.mandel_setup(w1, h1)
            for task_id in ('can1', 'can2', 'can3', 'can4'):
                self._queue_mandel_recursive_task(task_id, Rect(0, 0, w1, h1))

    def gui2_screen_preamble(self):
        self.gui2.restore_pristine()
        if not self.dragging and self.gui2.locking_object is self.canvas:
            self.gui2.set_lock_point(None)
        layout_needed = self._update_gui2_window_visibility()
        if layout_needed:
            self._layout_gui2_sim_windows()
        self.set_mandel_task_buttons_disabled(self.s2.tasks_busy_match_any(*Demo.mandel_task_ids))

    def gui2_panel_event_handler(self, event):
        if event.type == Event.Widget:
            if event.widget_id == 'back':
                self.state_manager.switch_context('gui1')
            return
        self._handle_common_exit_events(event)

    def _handle_common_exit_events(self, event):
        if event.type == Event.KeyDown and event.key == K_ESCAPE:
            self.state_manager.set_running(False)
        elif event.type == Event.Quit:
            self.state_manager.set_running(False)

    # main entry point of the program, invokes the engine
    def run(self):
        """Run the application using the Engine with StateManager contexts."""
        self.engine.run()

    # gui1 and shared screen helpers
    def _create_gui1_screen_widgets_layout(self, gui, base_x, base_y, disabled=False):
        widget_height = 28
        slider_range = 200
        integer_slider_range = 24
        slider_width = 420
        slider_height = 48
        v_slider_width = 48
        v_slider_height = 220
        id_prefix = 'disabled' if disabled else 'screen'
        title = 'Disabled Widgets' if disabled else 'Widget Demos'
        screen_widgets_area_height = 340 + slider_height
        screen_widgets_right_edge = base_x + 718
        demo_canvas_size = screen_widgets_area_height
        demo_canvas_x = screen_widgets_right_edge + 40
        demo_canvas_y = base_y + 34
        frame_rect = Rect(base_x + 316, base_y + 136, 132, 76)
        demo_canvas_rect = Rect(demo_canvas_x, demo_canvas_y, demo_canvas_size, demo_canvas_size)

        def maybe_disable(widget, disable_widget=True):
            if disabled and disable_widget:
                widget.disabled = True
            return widget

        # heading and basic widget samples
        gui.label((base_x, base_y), title, True)
        maybe_disable(
            gui.button(
                f'{id_prefix}_demo_button',
                Rect(base_x, base_y + 34, 138, widget_height),
                ButtonStyle.Round,
                'Button',
            )
        )
        maybe_disable(
            gui.toggle(
                f'{id_prefix}_demo_toggle',
                Rect(base_x + 148, base_y + 34, 146, widget_height),
                ButtonStyle.Box,
                False,
                'Toggle On',
                'Toggle Off',
            )
        )
        maybe_disable(
            gui.image(
                f'{id_prefix}_demo_image',
                Rect(base_x + 316, base_y + 34, 96, 96),
                'realize.png',
                False,
            )
        )
        maybe_disable(
            gui.frame(
                f'{id_prefix}_demo_frame',
                frame_rect,
            )
        )
        maybe_disable(gui.label((frame_rect.x + 10, frame_rect.y + 8), 'Frame', True))
        maybe_disable(
            gui.canvas(
                f'{id_prefix}_demo_canvas',
                demo_canvas_rect,
            )
        )
        maybe_disable(gui.label((demo_canvas_rect.x + 10, demo_canvas_rect.y + 8), 'Canvas', True))

        # Mini style showcase to the right of the canvas.
        style_showcase_x = demo_canvas_rect.right + 24
        style_showcase_y = base_y + 34
        style_row_height = 34
        style_label_w = 96
        style_widget_w = 108
        style_widget_gap = 8
        maybe_disable(gui.label((style_showcase_x, style_showcase_y - 24), 'Styles', True), disable_widget=False)
        style_rows = (
            ('Box', ButtonStyle.Box),
            ('Round', ButtonStyle.Round),
            ('Angle', ButtonStyle.Angle),
            ('Radio', ButtonStyle.Radio),
            ('Check', ButtonStyle.Check),
        )
        for row, (style_name, style_kind) in enumerate(style_rows):
            row_y = style_showcase_y + (row * style_row_height)
            style_key = style_name.lower()
            maybe_disable(gui.label((style_showcase_x, row_y + 6), style_name, True))
            group_x = style_showcase_x + style_label_w
            button_x = group_x + style_widget_w + style_widget_gap
            toggle_x = button_x + style_widget_w + style_widget_gap
            maybe_disable(
                gui.button_group(
                    f'{id_prefix}_style_group_{style_key}',
                    f'{id_prefix}_style_group_{style_key}_a',
                    Rect(group_x, row_y, style_widget_w, widget_height),
                    style_kind,
                    'Group',
                )
            )
            maybe_disable(
                gui.button(
                    f'{id_prefix}_style_button_{style_key}',
                    Rect(button_x, row_y, style_widget_w, widget_height),
                    style_kind,
                    'Button',
                )
            )
            maybe_disable(
                gui.toggle(
                    f'{id_prefix}_style_toggle_{style_key}',
                    Rect(toggle_x, row_y, style_widget_w, widget_height),
                    style_kind,
                    False,
                    'Toggle',
                    'Toggle',
                )
            )

        # grouped button samples
        maybe_disable(gui.label((base_x, base_y + 74), 'Group One', True))
        for index, label in enumerate(('One A', 'One B', 'One C')):
            maybe_disable(
                gui.button_group(
                    f'{id_prefix}_demo_group_a',
                    f'{id_prefix}_demo_group_a{index + 1}',
                    Rect(base_x, base_y + 96 + (34 * index), 132, widget_height),
                    ButtonStyle.Radio,
                    label,
                )
            )
        maybe_disable(gui.label((base_x + 150, base_y + 74), 'Group Two', True))
        for index, label in enumerate(('Two A', 'Two B', 'Two C')):
            maybe_disable(
                gui.button_group(
                    f'{id_prefix}_demo_group_b',
                    f'{id_prefix}_demo_group_b{index + 1}',
                    Rect(base_x + 150, base_y + 96 + (34 * index), 132, widget_height),
                    ButtonStyle.Check,
                    label,
                )
            )

        v_scroll_x = base_x + 460
        v_scroll_y = base_y + 34
        v_scroll_width = 20
        v_scroll_height = 180
        v_scroll_gap = 8
        v_scroll_styles = (
            ('skip', ArrowPosition.Skip),
            ('split', ArrowPosition.Split),
            ('near', ArrowPosition.Near),
            ('far', ArrowPosition.Far),
        )
        for index, (style_name, arrow_position) in enumerate(v_scroll_styles):
            scrollbar_id = f'{id_prefix}_demo_scroll_v_{style_name}'
            if arrow_position == ArrowPosition.Split:
                scrollbar_id = f'{id_prefix}_demo_scroll_v'
                if disabled:
                    scrollbar_id = 'disabled_demo_scrollbar'
            maybe_disable(
                gui.scrollbar(
                    scrollbar_id,
                    Rect(v_scroll_x + (index * (v_scroll_width + v_scroll_gap)), v_scroll_y, v_scroll_width, v_scroll_height),
                    Orientation.Vertical,
                    arrow_position,
                    (100, 0, 30, 10),
                )
            )

        h_scroll_y = base_y + 220
        h_scroll_gap = 8
        h_scroll_styles = (
            ('skip', ArrowPosition.Skip),
            ('split', ArrowPosition.Split),
            ('near', ArrowPosition.Near),
            ('far', ArrowPosition.Far),
        )
        h_scroll_count = len(h_scroll_styles)
        h_scroll_start_x = base_x
        h_scroll_right_x = v_scroll_x + ((h_scroll_count - 1) * (v_scroll_width + v_scroll_gap)) + v_scroll_width
        h_scroll_total_width = h_scroll_right_x - h_scroll_start_x
        h_scroll_width = (h_scroll_total_width - ((h_scroll_count - 1) * h_scroll_gap)) // h_scroll_count
        for index, (style_name, arrow_position) in enumerate(h_scroll_styles):
            scrollbar_id = f'{id_prefix}_demo_scroll_h_{style_name}'
            if arrow_position == ArrowPosition.Split:
                scrollbar_id = f'{id_prefix}_demo_scroll_h'
            maybe_disable(
                gui.scrollbar(
                    scrollbar_id,
                    Rect(h_scroll_start_x + (index * (h_scroll_width + h_scroll_gap)), h_scroll_y, h_scroll_width, 20),
                    Orientation.Horizontal,
                    arrow_position,
                    (100, 0, 30, 10),
                )
            )

        # slider samples
        h_float_y = base_y + 270
        h_int_y = base_y + 328
        h_slider_float = maybe_disable(
            gui.slider(
                f'{id_prefix}_h_slider_float',
                Rect(base_x, h_float_y, slider_width, slider_height),
                Orientation.Horizontal,
                slider_range,
                0.0,
                False,
            )
        )
        h_slider_int = maybe_disable(
            gui.slider(
                f'{id_prefix}_h_slider_int',
                Rect(base_x, h_int_y, slider_width, slider_height),
                Orientation.Horizontal,
                integer_slider_range,
                0,
                True,
            )
        )
        maybe_disable(gui.label((base_x, h_float_y - 18), 'H Slider Float', True))
        maybe_disable(gui.label((base_x, h_int_y - 18), 'H Slider Integer Snap', True))
        h_slider_float_value = maybe_disable(gui.label((base_x + slider_width + 12, h_float_y + 12), '0.00', True))
        h_slider_int_value = maybe_disable(gui.label((base_x + slider_width + 12, h_int_y + 12), '0', True))

        v_title_top = v_scroll_y
        v_slider_label_gap = 2
        v_float_x = base_x + 580
        v_slider_column_gap = 32
        v_int_x = v_float_x + v_slider_width + v_slider_column_gap
        v_title_float = maybe_disable(gui.label((v_float_x - 8, v_title_top), 'V Float', True))
        v_title_int = maybe_disable(gui.label((v_int_x - 12, v_title_top), 'V Int Snap', True))
        v_title_bottom = max(v_title_float.draw_rect.bottom, v_title_int.draw_rect.bottom)
        v_slider_y = v_title_bottom + v_slider_label_gap
        v_slider_bottom_gap = 1
        lower_h_slider_bottom = h_slider_int.draw_rect.bottom - 10
        v_slider_float_value = maybe_disable(gui.label((v_float_x - 6, 0), '0.00', True))
        v_slider_int_value = maybe_disable(gui.label((v_int_x + 8, 0), '0', True))
        v_slider_float_value.position = (
            v_float_x + ((v_slider_width - v_slider_float_value.draw_rect.width) // 2),
            lower_h_slider_bottom - v_slider_float_value.draw_rect.height,
        )
        v_slider_int_value.position = (
            v_int_x + ((v_slider_width - v_slider_int_value.draw_rect.width) // 2),
            lower_h_slider_bottom - v_slider_int_value.draw_rect.height,
        )
        v_value_top = min(v_slider_float_value.draw_rect.top, v_slider_int_value.draw_rect.top)
        v_slider_height = max(80, v_value_top - v_slider_bottom_gap - v_slider_y)
        v_slider_float = maybe_disable(
            gui.slider(
                f'{id_prefix}_v_slider_float',
                Rect(v_float_x, v_slider_y, v_slider_width, v_slider_height),
                Orientation.Vertical,
                slider_range,
                0.0,
                False,
            )
        )
        v_slider_int = maybe_disable(
            gui.slider(
                f'{id_prefix}_v_slider_int',
                Rect(v_int_x, v_slider_y, v_slider_width, v_slider_height),
                Orientation.Vertical,
                integer_slider_range,
                0,
                True,
            )
        )

        if not disabled:
            self.h_slider_float = h_slider_float
            self.h_slider_int = h_slider_int
            self.h_slider_float_value = h_slider_float_value
            self.h_slider_int_value = h_slider_int_value
            self.v_slider_float = v_slider_float
            self.v_slider_int = v_slider_int
            self.v_slider_float_value = v_slider_float_value
            self.v_slider_int_value = v_slider_int_value
            self._v_slider_value_label_bottom = lower_h_slider_bottom
            self._remember_slider_label_center(
                self.h_slider_float_value,
                self.h_slider_float_value.draw_rect.center,
            )
            self._remember_slider_label_center(
                self.h_slider_int_value,
                self.h_slider_int_value.draw_rect.center,
            )
            self._remember_slider_label_center(
                self.v_slider_float_value,
                (self.v_slider_float.draw_rect.centerx, self.v_slider_float_value.draw_rect.centery),
            )
            self._remember_slider_label_center(
                self.v_slider_int_value,
                (self.v_slider_int.draw_rect.centerx, self.v_slider_int_value.draw_rect.centery),
            )

    def _center_label_to_point(self, label, center_point):
        center_x, center_y = center_point
        label.position = (
            int(round(center_x - (label.draw_rect.width / 2))),
            int(round(center_y - (label.draw_rect.height / 2))),
        )

    def _remember_slider_label_center(self, label, center_point):
        self._slider_label_centers[label] = center_point
        self._center_label_to_point(label, center_point)

    def _center_slider_label(self, label):
        center_point = self._slider_label_centers.get(label)
        if center_point is not None:
            self._center_label_to_point(label, center_point)

    def _update_gui1_window_visibility(self):
        self.button_group_win.visible = self.buttons_toggle.pushed

    def _update_gui2_window_visibility(self):
        life_visible = self.gui2_life_window_toggle.pushed
        mandel_visible = self.gui2_mandel_window_toggle.pushed
        layout_needed = False
        if self.life_win.visible != life_visible:
            self.life_win.visible = life_visible
            layout_needed = True
        if self.mandel_win.visible != mandel_visible:
            self.mandel_win.visible = mandel_visible
            layout_needed = True
        return layout_needed

    def _layout_gui2_sim_windows(self):
        life_visible = self.life_win.visible
        mandel_visible = self.mandel_win.visible
        if not life_visible and not mandel_visible:
            return
        gap = 16
        y_pos = (self.screen_rect.height - self.life_win.height) // 2
        if life_visible and mandel_visible:
            total_width = self.life_win.width + gap + self.mandel_win.width
            left_x = (self.screen_rect.width - total_width) // 2
            self.life_win.position = (left_x, y_pos)
            self.mandel_win.position = (left_x + self.life_win.width + gap, y_pos)
            return
        centered_x = (self.screen_rect.width - self.life_win.width) // 2
        if life_visible:
            self.life_win.position = (centered_x, y_pos)
        if mandel_visible:
            self.mandel_win.position = (centered_x, y_pos)

    def update_slider_labels(self):
        self.h_slider_float_value.set_label(f'{self.h_slider_float.value:.2f}')
        self.h_slider_int_value.set_label(f'{int(round(self.h_slider_int.value))}')
        self.v_slider_float_value.set_label(f'{self.v_slider_float.value:.2f}')
        self.v_slider_int_value.set_label(f'{int(round(self.v_slider_int.value))}')
        self._center_slider_label(self.h_slider_float_value)
        self._center_slider_label(self.h_slider_int_value)
        v_bottom = getattr(self, '_v_slider_value_label_bottom', self.h_slider_int.draw_rect.bottom)
        self.v_slider_float_value.position = (
            self.v_slider_float.draw_rect.centerx - (self.v_slider_float_value.draw_rect.width // 2),
            v_bottom - self.v_slider_float_value.draw_rect.height,
        )
        self.v_slider_int_value.position = (
            self.v_slider_int.draw_rect.centerx - (self.v_slider_int_value.draw_rect.width // 2),
            v_bottom - self.v_slider_int_value.draw_rect.height,
        )

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
        self.gui_do_label.position = (int(round(x)), int(round(y)))

    def handle_canvas_overflow(self, _dropped_now, _dropped_total):
        while self.canvas.read_event() is not None:
            pass

    # life methods
    def handle_Canvas(self):
        # read the event from the canvas widget
        c_event = self.canvas.read_event()
        if c_event is not None:
            # parse that event by kind and parameters
            if c_event.type == CanvasEvent.MouseButtonDown:
                # left-mouse button toggles the clicked cell when over the canvas
                if c_event.button == 1 and c_event.pos is not None:
                    self.toggle_life_cell_at_canvas_pos(c_event.pos)
                # right-mouse button pressed, enter dragging state
                if c_event.button == 3:
                    self.dragging = True
                    self.gui2.set_cursor('hand')
                    self.gui2.set_lock_point(self.canvas)
            elif c_event.type == CanvasEvent.MouseButtonUp:
                # right-mouse button released, exit dragging state
                if c_event.button == 3:
                    self.dragging = False
                    self.gui2.set_cursor('normal')
                    self.gui2.set_lock_point(None)
            elif c_event.type == CanvasEvent.MouseMotion:
                # if dragging then track relative position
                if self.dragging and c_event.rel is not None:
                    x, y = c_event.rel[0], c_event.rel[1]
                    self.origin_x -= x
                    self.origin_y -= y
            elif c_event.type == CanvasEvent.MouseWheel:
                # handle the mouse wheel
                if c_event.y is not None:
                    old_size = self.cell_size
                    new_size = max(2, min(24, old_size + (c_event.y * 2)))
                    if new_size != old_size:
                        if self.gui2.mouse_point_locked and self.gui2.lock_point_pos is not None:
                            # During point-lock dragging, anchor zoom to the rendered (locked) cursor.
                            lock_x, lock_y = self.gui2.convert_to_window(self.gui2.lock_point_pos, self.canvas.window)
                            mouse_x = lock_x - self.canvas_rect.x
                            mouse_y = lock_y - self.canvas_rect.y
                        else:
                            mouse_x, mouse_y = (c_event.pos if c_event.pos is not None else self.canvas_rect.center)
                        # Keep the world position under the mouse fixed while scaling.
                        self.origin_x = mouse_x - ((mouse_x - self.origin_x) / old_size) * new_size
                        self.origin_y = mouse_y - ((mouse_y - self.origin_y) / old_size) * new_size
                        self.cell_size = new_size
                        self.life_zoom_slider.value = (new_size // 2) - 1
                        self._life_zoom_slider_last_value = int(self.life_zoom_slider.value)

    def toggle_life_cell_at_canvas_pos(self, canvas_pos):
        x_pos, y_pos = canvas_pos
        if not (0 <= x_pos < self.canvas_rect.width and 0 <= y_pos < self.canvas_rect.height):
            return
        cell_x = math.floor((x_pos - self.origin_x) / self.cell_size)
        cell_y = math.floor((y_pos - self.origin_y) / self.cell_size)
        cell = (cell_x, cell_y)
        if cell in self.life:
            self.life.remove(cell)
        else:
            self.life.add(cell)

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
            pop = population(cell)
            if pop in (2, 3):
                   new_life.add(cell)
            # Check all the neighbours of this cell
            for new_cell in Demo.neighbours:
                test_cell = (cell[0] + new_cell[0],
                             cell[1] + new_cell[1])
                if population(test_cell) == 3:
                   new_life.add(test_cell)
        # Replace the old set with the new
        self.life = new_life

    def life_reset(self):
        default_zoom = 6
        self.origin_x, self.origin_y = self.canvas_rect.centerx, self.canvas_rect.centery
        self.cell_size = default_zoom * 2
        self.life_zoom_slider.value = default_zoom - 1
        self._life_zoom_slider_last_value = int(self.life_zoom_slider.value)
        self.toggle_life.pushed = False
        # the starting configuration of the Life grid
        self.life = set({(0, 0), (0, -1), (1, -1), (-1, 0), (0, 1)})

    def draw_life(self):
        # Draw contents of the life cells onto the canvas surface
        self.canvas_surface.set_clip(Rect(1, 1, self.canvas_rect.width - 2, self.canvas_rect.height - 2))
        trim = 0 if self.cell_size == 2 else 1
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
                self.canvas_surface.fill(colours['full'], Rect(xpos, ypos, size_x - trim, size_y - trim))
        self.canvas_surface.set_clip(None)

    # mandelbrot methods
    def clear_mandel_surfaces(self):
        self.mandel_canvas.canvas.fill(colours['medium'])
        self.canvas1.canvas.fill(colours['medium'])
        self.canvas2.canvas.fill(colours['medium'])
        self.canvas3.canvas.fill(colours['medium'])
        self.canvas4.canvas.fill(colours['medium'])

    def set_mandel_task_buttons_disabled(self, disabled):
        for button in self.mandel_task_buttons:
            button.disabled = disabled

    def _show_single_mandel_canvas(self):
        # Show the primary Mandelbrot canvas and hide split panes.
        self.gui2.hide_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
        self.gui2.show_widgets(self.mandel_canvas)
        self.clear_mandel_surfaces()

    def _prepare_mandel_single_canvas_run(self):
        # Disable launch buttons while work is in flight.
        self.set_mandel_task_buttons_disabled(True)
        self._show_single_mandel_canvas()

    def _prepare_mandel_split_canvas_run(self):
        # Switch to split-pane view for per-canvas rendering tasks.
        self.set_mandel_task_buttons_disabled(True)
        self.gui2.hide_widgets(self.mandel_canvas)
        self.gui2.show_widgets(self.canvas1, self.canvas2, self.canvas3, self.canvas4)
        self.clear_mandel_surfaces()

    def _queue_mandel_recursive_task(self, task_id, rect):
        # Route task progress through a per-task callback that draws incremental updates.
        self.s2.add_task(task_id, self.mandel_recursive, rect,
                         message_method=self.make_mandel_progress_handler(task_id))

    def mandel_setup(self, width, height):
        # Precompute viewport and complex-plane mapping for workers.
        self.max_iter = 128
        self.maximum_iters = self.max_iter - 1
        self.mandel_width, self.mandel_height = width, height
        self.center = -0.7 + 0.0j
        extent = 2.5 + 2.5j
        self.scale = max((extent / self.mandel_width).real, (extent / self.mandel_height).imag)

    def handle_mandel_task_event(self, event):
        task_id = getattr(event, 'id', None)
        if task_id is None:
            return
        if getattr(event, 'error', None):
            print(f'Task failed: id={task_id} error={event.error}', file=sys.stderr)
        if task_id in Demo.mandel_task_ids:
            # Consume buffered result payloads for finished/updated tasks.
            self.s2.pop_result(task_id)
            if not self.s2.tasks_busy_match_any(*Demo.mandel_task_ids):
                # Re-enable controls only when all Mandelbrot tasks have drained.
                self.set_mandel_task_buttons_disabled(False)

    def make_mandel_progress_handler(self, task_id):
        def handler(result):
            # Execute on main thread: apply worker payload onto the target canvas.
            self.apply_mandel_result(task_id, result)
        return handler

    def apply_mandel_result(self, task_id, result):
        x, y, w, h, values = result
        canvas = self._mandel_canvas_for_task(task_id)
        if canvas is None:
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(canvas.get_width(), x + w)
        y1 = min(canvas.get_height(), y + h)
        if x1 <= x0 or y1 <= y0:
            return
        if (x0, y0, x1, y1) != (x, y, x + w, y + h):
            # Clip out-of-range payloads defensively before drawing.
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
            # Compact fill payload: single color value for the full region.
            canvas.fill(self.col(values), Rect(x, y, w, h))
            return
        idx = 0
        canvas.lock()
        try:
            # Expanded payload: per-pixel iteration counts.
            for y_pos in range(y, y + h):
                for x_pos in range(x, x + w):
                    canvas.set_at((x_pos, y_pos), self.col(values[idx]))
                    idx += 1
        finally:
            canvas.unlock()

    def _mandel_canvas_for_task(self, task_id):
        # Map task ids to their destination canvas surface.
        canvas_by_task = {
            'iter': self.mandel_canvas.canvas,
            'recu': self.mandel_canvas.canvas,
            '1': self.mandel_canvas.canvas,
            '2': self.mandel_canvas.canvas,
            '3': self.mandel_canvas.canvas,
            '4': self.mandel_canvas.canvas,
            'can1': self.canvas1.canvas,
            'can2': self.canvas2.canvas,
            'can3': self.canvas3.canvas,
            'can4': self.canvas4.canvas,
        }
        return canvas_by_task.get(task_id)

    def col(self, k):
        return (0, 0, 0) if k == self.maximum_iters else Demo.cols[k % 16]

    def mandel_iterative(self, task_id):
        # Iterative renderer sends scanlines in small row chunks for responsive updates.
        rect = Rect(0, 0, self.mandel_width, self.mandel_height)
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
                self.s2.send_message(task_id, (x, chunk_start_y, w, rows_in_chunk, row_values))
                chunk_start_y = y_pos + 1
                row_values = []
        if row_values:
            rows_in_chunk = y + h - chunk_start_y
            self.s2.send_message(task_id, (x, chunk_start_y, w, rows_in_chunk, row_values))
        return None

    def mandel_recursive(self, task_id, item):
        # Recursive renderer receives a region and adaptively subdivides it.
        x, y, w, h = item
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.mandel_width, x + w)
        y1 = min(self.mandel_height, y + h)
        if x1 <= x0 or y1 <= y0:
            return None
        x, y, w, h = x0, y0, x1 - x0, y1 - y0
        self.recursive_region(task_id, x, y, w, h)
        return None

    def recursive_region(self, task_id, x_pos, y_pos, width, height):
        if width <= 0 or height <= 0:
            return
        top_left = self.pixel(x_pos, y_pos)
        accuracy = 2
        not_hit = True
        # Edge-uniformity probe: if edges match, fill block without per-pixel recursion.
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
            self.fill_region(task_id, x_pos, y_pos, width, height, top_left)
            return
        if width > 2 or height > 2:
            # Subdivide into quadrants until regions are uniform or tiny.
            half_x = (width + (width % 2)) // 2
            half_y = (height + (height % 2)) // 2
            self.recursive_region(task_id, x_pos, y_pos, half_x, half_y)
            self.recursive_region(task_id, x_pos + half_x, y_pos, width - half_x, half_y)
            self.recursive_region(task_id, x_pos + half_x, y_pos + half_y, width - half_x, height - half_y)
            self.recursive_region(task_id, x_pos, y_pos + half_y, half_x, height - half_y)
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
        self.publish_pixel_block(task_id, x_pos, y_pos, width, height, block_values)

    def fill_region(self, task_id, x_pos, y_pos, width, height, value):
        # Send a compact fill payload so the GUI thread can draw this block with one fill call.
        self.s2.send_message(task_id, (x_pos, y_pos, width, height, value))

    def publish_pixel_block(self, task_id, x_pos, y_pos, width, height, block_values):
        # Small explicit block payload for base-case non-uniform regions.
        self.s2.send_message(task_id, (x_pos, y_pos, width, height, block_values))

    def pixel(self, x, y):
        # Convert screen-space pixel to complex-plane point and iterate z = z^2 + c.
        c = self.center + (x - self.mandel_width // 2 + (y - self.mandel_height // 2) * 1j) * self.scale
        z = 0
        for k in range(self.max_iter):
            z = z ** 2 + c
            if (z * z.conjugate()).real > 4.0:
                break
        return k

if __name__ == '__main__':
    Demo().run()
