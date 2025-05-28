import pygame
from math import cos, sin, radians
from random import randrange, choice
from pygame import FULLSCREEN, SCALED, QUIT
from pygame import Rect
from gui import GuiManager, Window, Label, Frame, FrameState, Button, PushButtonGroup, Scrollbar, PushButtonKind
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
        set_cursor((4, 0), 'cursors', 'Icons8_cursor.png')
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
        frame = Frame('panel', rec)
        add(frame)
        set_font('gui_do')
        add(Label(((x + centre(w, 120)), y + 40), 'gui_do'))
        set_font('normal')
        # horizontal scrollbar
        sb4 = Scrollbar('S1', Rect(x + 10, y + h - 30, 180, 20), True)
        sb4.set(100, 0, 30)
        add(sb4)
        # vertical scrollbar
        sb3 = Scrollbar('S2', Rect(x + w - 30, y + 40, 20, 150), False)
        sb3.set(100, 0, 30)
        add(sb3)
        set_grid_properties((x + 10, y + 10), 100, 20, 4)
        add(Button('exit', gridded(0, 0), 'Exit'), self.exit)
        self.pb_label = Label(gridded(1, 0), 'N/A')
        add(self.pb_label)
        set_grid_properties((x + 10, y + 110), 86, 20, 4)
        self.pb = PushButtonGroup('One', gridded(0, 0), 'One', 'pb', PushButtonKind.BOX)
        add(self.pb)
        add(PushButtonGroup('Two', gridded(1, 0), 'Two', 'pb', PushButtonKind.RADIO))
        add(PushButtonGroup('Three', gridded(0, 1), 'Three', 'pb', PushButtonKind.RADIO))
        add(PushButtonGroup('Four', gridded(1, 1), 'Four', 'pb', PushButtonKind.BOX))
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
        self.pb7 = PushButtonGroup('PB1', gridded(1, 0), 'PushButton', 'pb1', PushButtonKind.BOX)
        pb8 = PushButtonGroup('PB2', gridded(1, 1), 'PushButton', 'pb1', PushButtonKind.BOX)
        pb9 = PushButtonGroup('PB3', gridded(1, 2), 'PushButton', 'pb1', PushButtonKind.BOX)
        add(self.pb7)
        add(pb8)
        add(pb9)
        # pushbutton radios
        self.pb10 = PushButtonGroup('PR1', gridded(2, 0), 'RadioButton', 'pb2', PushButtonKind.RADIO)
        pb11 = PushButtonGroup('PR2', gridded(2, 1), 'RadioButton', 'pb2', PushButtonKind.RADIO)
        pb12 = PushButtonGroup('PR3', gridded(2, 2), 'RadioButton', 'pb2', PushButtonKind.RADIO)
        add(self.pb10)
        add(pb11)
        add(pb12)
        # labels
        self.window_label_button = Label(gridded(1, 3), 'N/A')
        self.window_label_radio = Label(gridded(2, 3), 'N/A')
        add(self.window_label_button)
        add(self.window_label_radio)
        # horizontal scrollbar
        sb3 = Scrollbar('S3', Rect(x + 10, y + height - 30, frame.rect.right - 45 - frame.rect.x, 20), True)
        sb3.set(100, 0, 30)
        add(sb3)
        # vertical scrollbar
        sb4 = Scrollbar('S4', Rect(frame.rect.right - 30, y + 10, 20, frame.rect.bottom - 20 - frame.rect.y), False)
        sb4.set(100, 0, 30)
        add(sb4)
        # add a grid of windows
        for x in range(15):
            for y in range(9):
                self.make_window(10 + (x * 125) + x, 30 + (y * 90) + y, 115, 55,
                                 f'{x},{y}', f'Win {x * 5 + y + 1}')
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
        boxes = 150
        size = 15
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
        frame = Frame('none', Rect(0, 0, 1, 1))
        frame.state = FrameState.ARMED
        frame.surface = self.screen
        # set a background image
        self.screen.blit(pygame.image.load(file_resource(
                                           'images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            self.pb_label.set_label(f'Push: {self.pb.read()}')
            self.window_label_button.set_label(f'PushBox: {self.pb7.read()}')
            self.window_label_radio.set_label(f'PushRadio: {self.pb10.read()}')
            bitmaps = []
            new_points = []
            # copy all the areas that are going to be overwritten
            for x, y, dx, dy in points:
                x += dx
                y += dy
                if x < 0 or x > self.screen.get_rect().width - size:
                    dx = -dx
                if y < 0 or y > self.screen.get_rect().height - size:
                    dy = -dy
                rec = Rect(x - 1, y - 1, size + 2, size + 2)
                new_points += [(x, y, dx, dy)]
                bitmap = copy_graphic_area(self.screen, rec)
                bitmaps.append((bitmap, rec))
            # then with the graphics saved draw on those areas
            for x, y, dx, dy in new_points:
                frame.rect = Rect(x, y, size, size)
                frame.draw()
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
        for event in pygame.event.get():
            # check if any gui objects handle the event
            widget_id = self.gui.handle_event(event)
            if widget_id != None:
                if widget_id == '<CONSUMED>':
                    continue
            else:
                if event.type == QUIT:
                    # handle window close widget or alt-f4 keypress
                    self.running = False

    # callback
    def exit(self):
        self.running = False

if __name__ == '__main__':
    Demo().run()
