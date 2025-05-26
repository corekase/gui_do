import pygame
from pygame import Rect, FULLSCREEN, SCALED, QUIT
from pygame.locals import KEYDOWN, K_ESCAPE
from gui import file_resource, centre, set_font, set_last_font
from gui import set_grid_properties, gridded
from gui import GuiManager, Window
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
        self.gui.set_surface(self.screen)
        set_font('normal')
        #
        # begin adding screen widgets
        # exit button
        self.gui.add(Button('exit', Rect(10, 1050, 140, 20), 'Exit'))
        # layout origin
        screen_rect = self.screen.get_rect()
        x, y = centre(screen_rect.width, 440), screen_rect.height - 155
        set_grid_properties((x + 10, y + 10), 140, 20, 4)
        # background frame
        self.gui.add(Frame('frame', Rect(x, y, 440, 145)))
        # regular buttons
        self.gui.add(Button('Button_1', gridded(0, 0), 'Button 1'))
        self.gui.add(Button('Button_2', gridded(0, 1), 'Button 2'))
        self.gui.add(Button('Button_3', gridded(0, 2), 'Button 3'))
        # pushbutton boxes
        self.pb1 = PushButtonGroup('SB1', gridded(1, 0), 'Button 1', 'pb1', PushButtonKind.BOX)
        pb2 = PushButtonGroup('SB2', gridded(1, 1), 'Button 2', 'pb1', PushButtonKind.BOX)
        pb3 = PushButtonGroup('SB3', gridded(1, 2), 'Button 3', 'pb1', PushButtonKind.BOX)
        self.gui.add(self.pb1)
        self.gui.add(pb2)
        self.gui.add(pb3)
        # pushbutton radios
        self.pb4 = PushButtonGroup('SR1', gridded(2, 0), 'Radio 1', 'pb2', PushButtonKind.RADIO)
        pb5 = PushButtonGroup('SR2', gridded(2, 1), 'Radio 2', 'pb2', PushButtonKind.RADIO)
        pb6 = PushButtonGroup('SR3', gridded(2, 2), 'Radio 3', 'pb2', PushButtonKind.RADIO)
        self.gui.add(self.pb4)
        self.gui.add(pb5)
        self.gui.add(pb6)
        # labels
        self.screen_label_button = Label(gridded(1, 3), 'N/A')
        self.screen_label_radio = Label(gridded(2, 3), 'N/A')
        self.gui.add(self.screen_label_button)
        self.gui.add(self.screen_label_radio)
        # horizontal scrollbar
        sb4 = Scrollbar('S1', Rect(x + 10, y + 115, 395, 20), True)
        sb4.set(100, 0, 30)
        self.gui.add(sb4)
        # vertical scrollbar
        sb3 = Scrollbar('S2', Rect(x + 410, y + 10, 20, 125), False)
        sb3.set(100, 0, 30)
        self.gui.add(sb3)
        # done adding screen widgets
        #
        # begin window layout, all window layouts have an x and y of 0's for the origin
        x, y, width, height = 0, 0, 440, 175
        # position of the window
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main', 'gui_do', (window_x, window_y), (width, height))
        # set grid layout properties
        set_grid_properties((x + 10, y + 45), 140, 20, 4)
        # done window layout
        #
        # begin adding window widgets
        # title label
        set_font('gui_do')
        label = Label((0, 0), 'gui_do')
        set_last_font()
        # main window label
        frame = Rect(x, y, width, height)
        label.rect.x = frame.x + centre(frame.width, label.rect.width)
        label.rect.y = y
        self.gui.add(label)
        # regular buttons
        self.gui.add(Button('Button_4', gridded(0, 0), 'Button 4'))
        self.gui.add(Button('Button_5', gridded(0, 1), 'Button 5'))
        self.gui.add(Button('Button_6', gridded(0, 2), 'Button 6'))
        # pushbutton boxes
        self.pb7 = PushButtonGroup('WB4', gridded(1, 0), 'Button 4', 'pb3', PushButtonKind.BOX)
        pb8 = PushButtonGroup('WB5', gridded(1, 1), 'Button 5', 'pb3', PushButtonKind.BOX)
        pb9 = PushButtonGroup('WB6', gridded(1, 2), 'Button 6', 'pb3', PushButtonKind.BOX)
        self.gui.add(self.pb7)
        self.gui.add(pb8)
        self.gui.add(pb9)
        # pushbutton radios
        self.pb10 = PushButtonGroup('WR4', gridded(2, 0), 'Radio 4', 'pb4', PushButtonKind.RADIO)
        pb11 = PushButtonGroup('WR5', gridded(2, 1), 'Radio 5', 'pb4', PushButtonKind.RADIO)
        pb12 = PushButtonGroup('WR6', gridded(2, 2), 'Radio 6', 'pb4', PushButtonKind.RADIO)
        self.gui.add(self.pb10)
        self.gui.add(pb11)
        self.gui.add(pb12)
        # labels
        self.window_label_button = Label(gridded(1, 3), 'N/A')
        self.window_label_radio = Label(gridded(2, 3), 'N/A')
        self.gui.add(self.window_label_button)
        self.gui.add(self.window_label_radio)
        # horizontal scrollbar
        sb3 = Scrollbar('S3', Rect(x + 10, y + height - 30, frame.right - 45 - frame.x, 20), True)
        sb3.set(100, 0, 30)
        self.gui.add(sb3)
        # vertical scrollbar
        sb4 = Scrollbar('S4', Rect(frame.right - 30, y + 10, 20, frame.bottom - 20 - frame.y), False)
        sb4.set(100, 0, 30)
        self.gui.add(sb4)
        # done adding window widgets
        #
        # gui setup done
        self.gui.set_active_object(None)
        # set cursor image
        self.gui.set_cursor_image('cursors', 'Icons8_cursor.png')
        # set cursor hotspot
        self.gui.set_cursor_hotspot((3, 0))
        # set a background image
        self.screen.blit(pygame.image.load(file_resource('images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # make the bigger font entry the default for new renders
        while self.running:
            # handle events
            self.handle_events()
            set_font('normal')
            self.screen_label_button.set_label(f'Button: {self.pb1.read()}')
            self.screen_label_radio.set_label(f'Radio: {self.pb4.read()}')
            self.window_label_button.set_label(f'Button: {self.pb7.read()}')
            self.window_label_radio.set_label(f'Radio: {self.pb10.read()}')
            set_last_font()
            # draw gui
            self.gui.draw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undraw gui
            self.gui.undraw_gui()
        # release resources
        pygame.quit()

    def handle_events(self):
        # handle the pygame event queue
        for event in pygame.event.get():
            # check if any gui objects handle the event
            gui_event = self.gui.handle_event(event)
            # if gui_event isn't None then it is a gui event
            if gui_event != None:
                # handle gui events
                if gui_event == 'exit':
                    # exit was clicked
                    self.running = False
                # elif other gui objects
            else:
                # handle window close widget or alt-f4 keypress
                if event.type == QUIT:
                    self.running = False
                # handle key presses
                elif event.type == KEYDOWN:
                    # handle escape key
                    if event.key == K_ESCAPE:
                        self.running = False
