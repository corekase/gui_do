import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import set_surface, file_resource, centre, load_font, set_font, set_last_font
from gui import set_grid_properties, gridded
from gui import set_active_object, set_cursor, add
from gui import GuiManager, GKind, Window
from gui import Frame, Label, Button, PushButtonGroup, PushButtonKind, Scrollbar

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
        set_surface(self.screen)
        # load fonts
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # manipulator to set one of the loaded font names
        set_font('normal')
        #
        # -> begin adding screen widgets
        #
        # exit button, uses a callback function
        add(Button('exit_callback', Rect(10, 1050, 140, 20), 'Exit (Callback)'), self.exit)
        # exit button, uses an event signal
        add(Button('exit_signal', Rect(160, 1050, 140, 20), 'Exit (Signal)'))
        # layout origin
        screen_rect = self.screen.get_rect()
        x, y = centre(screen_rect.width, 440), screen_rect.height - 155
        set_grid_properties((x + 10, y + 10), 140, 20, 4)
        # background frame
        add(Frame('none', Rect(x, y, 440, 145)))
        # regular buttons
        add(Button('Button_1', gridded(0, 0), 'Button 1'))
        add(Button('Button_2', gridded(0, 1), 'Button 2'))
        add(Button('Button_3', gridded(0, 2), 'Button 3'))
        # pushbutton boxes
        self.pb1 = add(PushButtonGroup('SB1', gridded(1, 0), 'Button 1', 'pb1', PushButtonKind.BOX))
        add(PushButtonGroup('SB2', gridded(1, 1), 'Button 2', 'pb1', PushButtonKind.BOX))
        add(PushButtonGroup('SB3', gridded(1, 2), 'Button 3', 'pb1', PushButtonKind.BOX))
        # pushbutton radios
        self.pb4 = add(PushButtonGroup('SR1', gridded(2, 0), 'Radio 1', 'pb2', PushButtonKind.RADIO))
        add(PushButtonGroup('SR2', gridded(2, 1), 'Radio 2', 'pb2', PushButtonKind.RADIO))
        add(PushButtonGroup('SR3', gridded(2, 2), 'Radio 3', 'pb2', PushButtonKind.RADIO))
        # labels
        self.screen_label_button = Label(gridded(1, 3), 'N/A')
        self.screen_label_radio = Label(gridded(2, 3), 'N/A')
        add(self.screen_label_button)
        add(self.screen_label_radio)
        # horizontal scrollbar
        sb4 = add(Scrollbar('S1', Rect(x + 10, y + 115, 395, 20), True))
        sb4.set(100, 0, 30)
        # vertical scrollbar
        sb3 = add(Scrollbar('S2', Rect(x + 410, y + 10, 20, 125), False))
        sb3.set(100, 0, 30)
        #
        # -> end adding screen widgets
        #
        # -> begin window layout, all window layouts have an x and y of 0's for the origin
        #
        x, y, width, height = 0, 0, 440, 175
        # position of the window
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main', 'gui_do', (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((x + 10, y + 45), 140, 20, 4)
        #
        # -> end window layout
        #
        # -> begin adding window widgets
        #
        # title label
        set_font('gui_do')
        label = Label((0, 0), 'gui_do')
        set_last_font()
        # main window label
        frame = Rect(x, y, width, height)
        label.rect.x = frame.x + centre(frame.width, label.rect.width)
        label.rect.y = y
        add(label)
        # regular buttons
        add(Button('Button_4', gridded(0, 0), 'Button 4'))
        add(Button('Button_5', gridded(0, 1), 'Button 5'))
        add(Button('Button_6', gridded(0, 2), 'Button 6'))
        # pushbutton boxes
        self.pb7 = add(PushButtonGroup('WB4', gridded(1, 0), 'Button 4', 'pb3', PushButtonKind.BOX))
        add(PushButtonGroup('WB5', gridded(1, 1), 'Button 5', 'pb3', PushButtonKind.BOX))
        add(PushButtonGroup('WB6', gridded(1, 2), 'Button 6', 'pb3', PushButtonKind.BOX))
        # pushbutton radios
        self.pb10 = add(PushButtonGroup('WR4', gridded(2, 0), 'Radio 4', 'pb4', PushButtonKind.RADIO))
        add(PushButtonGroup('WR5', gridded(2, 1), 'Radio 5', 'pb4', PushButtonKind.RADIO))
        add(PushButtonGroup('WR6', gridded(2, 2), 'Radio 6', 'pb4', PushButtonKind.RADIO))
        # labels
        self.window_label_button = add(Label(gridded(1, 3), 'N/A'))
        self.window_label_radio = add(Label(gridded(2, 3), 'N/A'))
        # horizontal scrollbar
        sb3 = add(Scrollbar('S3', Rect(x + 10, y + height - 30, frame.right - 45 - frame.x, 20), True))
        sb3.set(100, 0, 30)
        # vertical scrollbar
        sb4 = add(Scrollbar('S4', Rect(frame.right - 30, y + 10, 20, frame.bottom - 20 - frame.y), False))
        sb4.set(100, 0, 30)
        #
        # -> end adding window widgets
        #
        # -> begin window layout, all window layouts have an x and y of 0's for the origin
        #
        x, y, width, height = 0, 0, 115, 55
        # position of the window
        window_x = 50
        window_y = 150
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main2', 'Win 1', (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((x + 5, y + 5), 50, 20, 4)
        #
        # -> end window layout
        #
        # -> begin adding window widgets
        #
        add(Button('main2_Button_1', gridded(0, 0), 'One'))
        add(Button('main2_Button_2', gridded(0, 1), 'Two'))
        add(Button('main2_Button_3', gridded(1, 0), 'Three'))
        add(Button('main2_Button_4', gridded(1, 1), 'Four'))
        #
        # -> end adding window widgets
        #
        # -> begin window layout, all window layouts have an x and y of 0's for the origin
        #
        x, y, width, height = 0, 0, 115, 55
        # position of the window
        window_x = 50
        window_y = 250
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main3', 'Win 2', (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((x + 5, y + 5), 50, 20, 4)
        #
        # -> end window layout
        #
        # -> begin adding window widgets
        #
        add(Button('main3_Button_1', gridded(0, 0), 'One'))
        add(Button('main3_Button_2', gridded(0, 1), 'Two'))
        add(Button('main3_Button_3', gridded(1, 0), 'Three'))
        add(Button('main3_Button_4', gridded(1, 1), 'Four'))
        #
        # -> end adding window widgets
        #
        #
        # -> gui setup done
        #
        set_active_object(None)
        # set cursor image
        set_cursor((1, 1), 'cursors', 'Icons8_cursor.png')
        # set a background image
        self.screen.blit(pygame.image.load(file_resource('images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # set running flag
        self.running = True
        # drop test for consumed events
        self.drop_test_frame = Frame('drop_test', (0, 0, 30, 30))
        self.drop_test_frame.surface = self.screen

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            #
            # -> gui_do client program logic goes here
            #
            # -> gui_do client screen drawing code begins here
            #
            set_font('normal')
            self.screen_label_button.set_label(f'PushBox: {self.pb1.read()}')
            self.screen_label_radio.set_label(f'Radio: {self.pb4.read()}')
            self.window_label_button.set_label(f'PushBox: {self.pb7.read()}')
            self.window_label_radio.set_label(f'Radio: {self.pb10.read()}')
            #
            # -> gui_do client screen drawing code ends here
            #
            #
            # -> begin keep everything in this block
            #
            # draw gui
            self.gui.draw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undraw gui
            self.gui.undraw_gui()
            #
            # -> end keep everything in this block
            #
            # -> gui_do client screen undrawing code begins here
            #
            pass
            #
            # -> gui_do client screen undrawing code ends here
            #
        # release resources
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
                return
            if event.type == GKind.Widget:
                # handle signals
                if event.widget_id == 'exit_signal':
                    self.running = False
            elif event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # handle escape key
                    self.running = False
            # test whether mouse events are consumed when they are over a window or widget
            # if you are over a window or widget then you don't get the MouseButtonDown event
            elif event.type == GKind.MouseButtonDown:
                if event.button == 1:
                    x, y = event.pos
                    self.drop_test_frame.rect = Rect(x - (self.drop_test_frame.rect.width // 2),
                                                     y - (self.drop_test_frame.rect.height // 2),
                                                     self.drop_test_frame.rect.width, self.drop_test_frame.rect.height)
                    self.drop_test_frame.draw()
    # callbacks
    def exit(self):
        # called from gui_manager automatically
        self.running = False

if __name__ == '__main__':
    Demo().run()
