import pygame
from random import randrange, choice
from pygame import FULLSCREEN, SCALED, K_ESCAPE
from pygame import Rect
from gui import GKind, Label, Frame, FrState, Button, PushButtonGroup, ToggleButton
from gui import gui_init, Window, load_font, set_font, add, set_cursor, set_backdrop, restore_pristine
from gui import centre, set_grid_properties, gridded, Scrollbar

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
        #
        # create a gui manager and it makes the screen the active object
        #
        self.gui = gui_init(self.screen)
        #
        # blit a background image to the screen surface, also saves that into the pristine surface
        #
        set_backdrop('backdrop.jpg')
        #
        # set cursor image
        #
        set_cursor((1, 1), 'cursor.png')
        #
        # load fonts
        #
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        #
        # screen widgets
        #
        # manipulator to set one of the loaded font names
        set_font('normal')
        # dimensions of the screen widgets frame
        x, y, w, h = 10, self.screen.get_rect().height - 180, 228, 170
        rec = Rect(x, y, w, h)
        frame = add(Frame('panel', rec))
        # gui_do label
        set_font('gui_do')
        add(Label(((x + centre(w, 120)), y + 5), 'gui_do'))
        set_font('normal')
        # horizontal scrollbar
        sb1 = add(Scrollbar('S1', Rect(x + 10, y + h - 30, 180, 20), True, 1))
        sb1.set(100, 0, 30, 10)
        # vertical scrollbar
        sb2 = add(Scrollbar('S2', Rect(x + w - 30, y + 10, 20, 150), False, 1))
        sb2.set(100, 0, 30, 10)
        # fps controls
        self.fps_label = add(Label(Rect(x + 10, y + h - 110, 70, 20), 'N/A', 60))
        set_grid_properties((x + 10, y + h - 90), 70, 20, 5)
        self.fps_control = add(PushButtonGroup('60_fps', gridded(0, 0), '60 fps', 'fps', 1))
        add(PushButtonGroup('full_fps', gridded(1, 0), 'Uncapped', 'fps', 1))
        # exit button and boxes toggle
        set_grid_properties((x + 12, y + h - 60), 85, 20, 5)
        # exit button
        add(Button('exit', gridded(0, 0), 'Exit'), self.exit)
        # boxes toggle
        self.box_control = add(ToggleButton('toggle', gridded(1, 0), True, 'Boxes'))
        #
        # main window setup
        #
        # position of the window
        x, y, width, height = 0, 0, 440, 140
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('gui_do', (window_x, window_y + 400), (width, height))
        frame = Frame('none', Rect(0, 0, 440, 140))
        # set grid layout properties
        set_grid_properties((x + 10, y + 10), 140, 20, 4)
        # regular buttons
        add(Button('Button_1', gridded(0, 0), 'Button 1'))
        add(Button('Button_2', gridded(0, 1), 'Button 2'))
        add(Button('Button_3', gridded(0, 2), 'Button 3'))
        # pushbutton boxes
        self.window_push_box_widget = add(PushButtonGroup('Box 1', gridded(1, 0), 'Push Box 1', 'pb', 0))
        add(PushButtonGroup('Box 2', gridded(1, 1), 'Push Box 2', 'pb', 0))
        add(PushButtonGroup('Box 3', gridded(1, 2), 'Push Box 3', 'pb', 0))
        # pushbutton radios
        # save the graphic area under the radios and labels
        self.window_radio_box_widget = add(PushButtonGroup('Radio 1', gridded(2, 0), 'Push Radio 1', 'pr', 1))
        add(PushButtonGroup('Radio 2', gridded(2, 1), 'Push Radio 2', 'pr', 1))
        add(PushButtonGroup('Radio 3', gridded(2, 2), 'Push Radio 3', 'pr', 1))
        # labels
        self.window_pushbox_label = add(Label(gridded(1, 3), 'N/A', 50))
        self.window_radio_label = add(Label(gridded(2, 3), 'N/A', 50))
        # horizontal scrollbar
        sb3 = add(Scrollbar('S3', Rect(x + 10, y + height - 30, frame.rect.right - 45 - frame.rect.x, 20), True, 1))
        sb3.set(100, 0, 30, 10)
        # vertical scrollbar
        sb4 = add(Scrollbar('S4', Rect(frame.rect.right - 30, y + 10, 20, frame.rect.bottom - 20 - frame.rect.y), False, 1))
        sb4.set(100, 0, 30, 10)
        #
        # tiled windows setup
        #
        # add a grid of windows
        win_num = 0
        for y in range(9):
            for x in range(15):
                win_num += 1
                self.make_window(f'Win {win_num}', 10 + (x * 125) + x, 30 + (y * 90) + y, 115, 55)
        #
        # all done
        #
        # set running flag
        self.running = True

    def make_window(self, title, window_x, window_y, width, height):
        counter = 0
        Window(title, (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((5, 5), 50, 20, 4)
        counter += 1
        button_id = f'{title}.{window_x}.{window_y}.{counter}'
        add(Button(button_id, gridded(0, 0), 'One'))
        counter += 1
        button_id = f'{title}.{window_x}.{window_y}.{counter}'
        add(Button(button_id, gridded(1, 0), 'Two'))
        counter += 1
        button_id = f'{title}.{window_x}.{window_y}.{counter}'
        add(Button(button_id, gridded(0, 1), 'Three'))
        counter += 1
        button_id = f'{title}.{window_x}.{window_y}.{counter}'
        add(Button(button_id, gridded(1, 1), 'Four'))

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # number of boxes to draw on screen
        boxes = 200
        # setup a frame to draw on our surface
        size = 12
        frame = Frame('none', Rect(0, 0, size, size))
        frame.state = FrState.Armed
        # create our bitmap
        frame_bitmap = pygame.surface.Surface((size, size))
        # point the frame object at it
        frame.surface = frame_bitmap
        # and render onto that surface
        frame.draw()
        max_x, max_y = self.screen.get_rect().width - size, self.screen.get_rect().height - size
        areas = []
        for _ in range(boxes):
            x = randrange(0, self.screen.get_rect().width - size)
            y = randrange(0, self.screen.get_rect().height - size)
            dx = randrange(2, 7)
            dy = randrange(2, 7)
            if choice([True, False]):
                dx = -dx
            if choice([True, False]):
                dy = -dy
            areas.append((x, y, dx, dy))
        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            # handle program logic
            if self.fps_control.read() == '60_fps':
                fps = 60
            else:
                fps = 0
            self.fps_label.set_label(f'FPS: {round(clock.get_fps())}')
            self.window_pushbox_label.set_label(f'{self.window_push_box_widget.read()}')
            self.window_radio_label.set_label(f'{self.window_radio_box_widget.read()}')
            if self.box_control.read():
                new_areas = []
                for x, y, dx, dy in areas:
                    x += dx
                    y += dy
                    if x < 0 or x > max_x:
                        dx = -dx
                    if y < 0 or y > max_y:
                        dy = -dy
                    self.screen.blit(frame_bitmap, (x, y))
                    new_areas.append((x, y, dx, dy))
            #
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
            # undraw gui
            self.gui.undraw_gui()
            #
            # restore saved areas that were drawn over
            #
            if self.box_control.read():
                for x, y, dx, dy in new_areas:
                    area = Rect(x, y, size, size)
                    # restore a bitmap area from the screen's pristine bitmap to the main surface
                    restore_pristine(area)
                # swap the lists to start again
                areas = new_areas
        pygame.quit()

    def handle_events(self):
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
            if event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # handle escape key
                    self.running = False

    # callback
    def exit(self):
        self.running = False

if __name__ == '__main__':
    Demo().run()
