import pygame
from random import randrange, choice
from pygame import FULLSCREEN, SCALED, K_ESCAPE
from pygame import Rect
from gui import GuiManager, Window, GKind, Label, Frame, FrameState, Button, PushButtonGroup, Scrollbar, PushButtonKind
from gui import load_font, set_save, set_font, add, set_cursor, file_resource, copy_graphic_area
from gui import centre, set_grid_properties, gridded

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
        # create a gui manager and it makes the screen the active object
        self.gui = GuiManager()
        # set the drawing surface of the gui manager
        self.gui.set_surface(self.screen)
        # set cursor image
        set_cursor((1, 1), 'cursors', 'Icons8_cursor.png')
        # load fonts
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # manipulator to control whether a screen widget saves the graphic underneath it
        set_save(False)
        # manipulator to set one of the loaded font names
        set_font('normal')
        x, y, w, h = 10, self.screen.get_rect().height - 210, 228, 200
        rec = Rect(x, y, w, h)
        frame = add(Frame('panel', rec))
        set_font('gui_do')
        add(Label(((x + centre(w, 120)), y + 40), 'gui_do'))
        set_font('normal')
        # horizontal scrollbar
        sb4 = add(Scrollbar('S1', Rect(x + 10, y + h - 30, 180, 20), True))
        sb4.set(100, 0, 30)
        # vertical scrollbar
        sb3 = add(Scrollbar('S2', Rect(x + w - 30, y + 40, 20, 150), False))
        sb3.set(100, 0, 30)
        set_grid_properties((x + 10, y + 10), 100, 20, 4)
        add(Button('exit', gridded(0, 0), 'Exit'), self.exit)
        self.fps_label = add(Label(gridded(1, 0), 'N/A'))
        set_grid_properties((x + 10, y + 150), 70, 20, 4)
        self.fps_control = add(PushButtonGroup('60fps', gridded(0, 0), '60 fps', 'fps', PushButtonKind.RADIO))
        add(PushButtonGroup('fpsupcapped', gridded(1, 0), 'Uncapped', 'fps', PushButtonKind.RADIO))
        x, y, width, height = 0, 0, 440, 140
        # position of the window
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main', 'gui_do', (window_x, window_y + 400), (width, height))
        frame = Frame('none', Rect(0, 0, 440, 140))
        # set grid layout properties
        set_grid_properties((x + 10, y + 10), 140, 20, 4)
        # regular buttons
        add(Button('Button_1', gridded(0, 0), 'Button'))
        add(Button('Button_2', gridded(0, 1), 'Button'))
        add(Button('Button_3', gridded(0, 2), 'Button'))
        # pushbutton boxes
        self.window_push_box_widget = add(PushButtonGroup('Push 1', gridded(1, 0), 'PushButton', 'pb', PushButtonKind.BOX))
        add(PushButtonGroup('Push 2', gridded(1, 1), 'PushButton', 'pb', PushButtonKind.BOX))
        add(PushButtonGroup('Push 3', gridded(1, 2), 'PushButton', 'pb', PushButtonKind.BOX))
        # pushbutton radios
        self.window_radio_box_widget = add(PushButtonGroup('Radio 1', gridded(2, 0), 'RadioButton', 'pr', PushButtonKind.RADIO))
        add(PushButtonGroup('Radio 2', gridded(2, 1), 'RadioButton', 'pr', PushButtonKind.RADIO))
        add(PushButtonGroup('Radio 3', gridded(2, 2), 'RadioButton', 'pr', PushButtonKind.RADIO))
        # labels
        self.window_pushbox_label = add(Label(gridded(1, 3), 'N/A'))
        self.window_radio_label = add(Label(gridded(2, 3), 'N/A'))
        # horizontal scrollbar
        sb3 = add(Scrollbar('S3', Rect(x + 10, y + height - 30, frame.rect.right - 45 - frame.rect.x, 20), True))
        sb3.set(100, 0, 30)

        # vertical scrollbar
        sb4 = add(Scrollbar('S4', Rect(frame.rect.right - 30, y + 10, 20, frame.rect.bottom - 20 - frame.rect.y), False))
        sb4.set(100, 0, 30)
        # add a grid of windows
        win_num = 0
        for y in range(9):
            for x in range(15):
                win_num += 1
                self.make_window(10 + (x * 125) + x, 30 + (y * 90) + y, 115, 55,
                                 f'{x},{y}', f'Win {win_num}')
        # set running flag
        self.running = True

    def make_window(self, window_x, window_y, width, height, id, name):
        counter = 0
        Window(id, name, (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((5, 5), 50, 20, 4)
        counter += 1
        button_id = f'{id}{name}{window_x}{window_y}{counter}'
        add(Button(button_id, gridded(0, 0), 'One'))
        counter += 1
        button_id = f'{id}{name}{window_x}{window_y}{counter}'
        add(Button(button_id, gridded(1, 0), 'Two'))
        counter += 1
        button_id = f'{id}{name}{window_x}{window_y}{counter}'
        add(Button(button_id, gridded(0, 1), 'Three'))
        counter += 1
        button_id = f'{id}{name}{window_x}{window_y}{counter}'
        add(Button(button_id, gridded(1, 1), 'Four'))

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        boxes = 1000
        # setup a frame to draw on our surface
        size = 15
        frame = Frame('none', Rect(0, 0, size, size))
        frame.state = FrameState.ARMED
        # create our bitmap
        frame_bitmap = pygame.surface.Surface((size, size))
        # point the frame object at it
        frame.surface = frame_bitmap
        # and render onto that surface
        frame.draw()
        points = []
        for _ in range(boxes):
            x = randrange(0, self.screen.get_rect().width - size)
            y = randrange(0, self.screen.get_rect().height - size)
            dx = randrange(2, 7)
            dy = randrange(2, 7)
            if choice([True, False]):
                dx = -dx
            if choice([True, False]):
                dy = -dy
            points.append((x, y, dx, dy))
        # set a background image
        self.screen.blit(pygame.image.load(file_resource(
                                           'images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            if self.fps_control.read() == '60fps':
                fps = 60
            else:
                fps = 0
            self.fps_label.set_label(f'FPS: {round(clock.get_fps())}')
            self.window_pushbox_label.set_label(f'{self.window_push_box_widget.read()}')
            self.window_radio_label.set_label(f'{self.window_radio_box_widget.read()}')
            bitmaps = []
            new_points = []
            # copy all the areas that are going to be overwritten
            for x, y, dx, dy in points:
                x += dx
                y += dy
                if x < 0 or x > (self.screen.get_rect().width - size):
                    dx = -dx
                if y < 0 or y > (self.screen.get_rect().height - size):
                    dy = -dy
                rec = Rect(x - 1, y - 1, size + 2, size + 2)
                new_points += [(x, y, dx, dy)]
                bitmaps.append((copy_graphic_area(self.screen, rec), rec))
            # then with the graphics saved draw on those areas
            for x, y, dx, dy in new_points:
                self.screen.blit(frame_bitmap, Rect(x, y, size, size))
            # swap the lists to start again
            points = new_points
            # draw gui
            self.gui.draw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undraw gui
            self.gui.undraw_gui()
            # restore the saved areas that were drawn over
            for bitmap, rec in bitmaps:
                self.screen.blit(bitmap, rec)
        pygame.quit()

    def handle_events(self):
        # handle the pygame event queue
        for raw_event in pygame.event.get():
            # process event queue
            event = self.gui.handle_event(raw_event)
            if event.type == GKind.Pass:
                continue
            if event.type == GKind.Quit:
                # handle window close widget or alt-f4 keypress
                self.running = False
            if event.type == GKind.KeyDown:
                if event.key == K_ESCAPE:
                    self.running = False

    # callback
    def exit(self):
        self.running = False

if __name__ == '__main__':
    Demo().run()
