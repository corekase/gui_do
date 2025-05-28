import pygame
from math import cos, sin, radians
from random import randrange, choice
from pygame import FULLSCREEN, SCALED, QUIT
from pygame import Rect
from gui import GuiManager, Window, Label, Frame, Button, PushButtonGroup, Scrollbar, PushButtonKind
from gui import load_font, set_save, set_font, add, set_cursor, file_resource, copy_graphic_area
from gui import centre, set_grid_properties, set_last_font, gridded

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
        add(Button('a', gridded(1, 0), 'Button'))
        x, y, width, height = 0, 0, 440, 140
        # position of the window
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main', 'gui_do', (window_x, window_y), (width, height))
        frame = Frame('none', Rect(0, 0, 440, 140))
        # set grid layout properties
        set_grid_properties((x + 10, y + 10), 140, 20, 4)
        # regular buttons
        add(Button('Button_4', gridded(0, 0), 'Button 4'))
        add(Button('Button_5', gridded(0, 1), 'Button 5'))
        add(Button('Button_6', gridded(0, 2), 'Button 6'))
        # pushbutton boxes
        self.pb7 = PushButtonGroup('WB4', gridded(1, 0), 'Button 4', 'pb3', PushButtonKind.BOX)
        pb8 = PushButtonGroup('WB5', gridded(1, 1), 'Button 5', 'pb3', PushButtonKind.BOX)
        pb9 = PushButtonGroup('WB6', gridded(1, 2), 'Button 6', 'pb3', PushButtonKind.BOX)
        add(self.pb7)
        add(pb8)
        add(pb9)
        # pushbutton radios
        self.pb10 = PushButtonGroup('WR4', gridded(2, 0), 'Radio 4', 'pb4', PushButtonKind.RADIO)
        pb11 = PushButtonGroup('WR5', gridded(2, 1), 'Radio 5', 'pb4', PushButtonKind.RADIO)
        pb12 = PushButtonGroup('WR6', gridded(2, 2), 'Radio 6', 'pb4', PushButtonKind.RADIO)
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
        x, y, width, height = 0, 0, 115, 55
        # position of the window
        window_x = 50
        window_y = 150
        Window('main2', 'Win 1', (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((x + 5, y + 5), 50, 20, 4)
        add(Button('main2_Button_1', gridded(0, 0), 'One'))
        add(Button('main2_Button_2', gridded(0, 1), 'Two'))
        add(Button('main2_Button_3', gridded(1, 0), 'Three'))
        add(Button('main2_Button_4', gridded(1, 1), 'Four'))
        x, y, width, height = 0, 0, 115, 55
        # position of the window
        window_x = 50
        window_y = 250
        Window('main3', 'Win 2', (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((x + 5, y + 5), 50, 20, 4)
        add(Button('main3_Button_1', gridded(0, 0), 'One'))
        add(Button('main3_Button_2', gridded(0, 1), 'Two'))
        add(Button('main3_Button_3', gridded(1, 0), 'Three'))
        add(Button('main3_Button_4', gridded(1, 1), 'Four'))
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        boxes = 50
        size = 15
        points = []
        for _ in range(boxes):
            x = randrange(0, self.screen.get_rect().width - size)
            y = randrange(0, self.screen.get_rect().height - size)
            dx = randrange(3, 10)
            dy = randrange(3, 10)
            if choice([True, False]):
                dx = -dx
            if choice([True, False]):
                dy = -dy
            points.append([x, y, dx, dy])
        frame = Frame('none', Rect(0, 0, 1, 1))
        frame.surface = self.screen
        # set a background image
        self.screen.blit(pygame.image.load(file_resource(
                                           'images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            self.window_label_button.set_label(f'PushBox: {self.pb7.read()}')
            self.window_label_radio.set_label(f'Radio: {self.pb10.read()}')
            bitmaps = []
            new_points = []
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

            for x, y, dx, dy in new_points:
                frame.rect = Rect(x, y, size, size)
                frame.draw()
            points = new_points
            # draw gui
            self.gui.draw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undraw gui
            self.gui.undraw_gui()
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

    def exit(self):
        self.running = False

if __name__ == '__main__':
    Demo().run()
