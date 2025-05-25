import pygame
from pygame import Rect, FULLSCREEN, SCALED, QUIT
from pygame.locals import MOUSEMOTION, KEYDOWN, K_ESCAPE
from gui import GuiManager, PushButtonKind
from gui import Label, Button, PushButtonGroup, Scrollbar, Frame
from gui import file_resource, image_alpha, copy_graphic_area, centre, set_font, set_last_font
from gui import set_grid_properties, gridded
from gui import Window

class Demo:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface, if not using vsync adjust fps in run()
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED, vsync=1)
        # set window caption
        pygame.display.set_caption('gui_do')
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        # create a gui manager and it makes the screen the active object
        self.gui = GuiManager()
        self.gui.set_surface(self.screen)

        # begin adding screen widgets
        self.gui.add_widget(Button('exit', Rect(10, 1050, 120, 20), 'Exit'))
        x, y = 150, 100
        set_grid_properties((x, y), 140, 20, 4)
        self.gui.add_widget(Frame('frame', Rect(x - 10, y - 10, 440, 90)))
        self.gui.add_widget(Button('Button_A', gridded(0, 0), 'Button'))
        self.gui.add_widget(Button('Button_B', gridded(0, 1), 'Button'))
        self.gui.add_widget(Button('Button_C', gridded(0, 2), 'Button'))
        pb1a = PushButtonGroup('BB1', gridded(1, 0), 'Button 1', 'pb3', PushButtonKind.BOX)
        pb2a = PushButtonGroup('BB2', gridded(1, 1), 'Button 2', 'pb3', PushButtonKind.BOX)
        pb3a = PushButtonGroup('BB3', gridded(1, 2), 'Button 3', 'pb3', PushButtonKind.BOX)
        self.gui.add_widget(pb1a)
        self.gui.add_widget(pb2a)
        self.gui.add_widget(pb3a)
        pb1b = PushButtonGroup('BC1', gridded(2, 0), 'Radio 1', 'pb4', PushButtonKind.RADIO)
        pb2b = PushButtonGroup('BC2', gridded(2, 1), 'Radio 2', 'pb4', PushButtonKind.RADIO)
        pb3b = PushButtonGroup('BC3', gridded(2, 2), 'Radio 3', 'pb4', PushButtonKind.RADIO)
        self.gui.add_widget(pb1b)
        self.gui.add_widget(pb2b)
        self.gui.add_widget(pb3b)
        # done adding screen widgets

        # begin adding window widgets
        # layout origin
        x = y = 0
        # width and height of the first window
        width = 440
        height = 175
        # position of the window
        x1 = centre(self.screen.get_rect().width, width)
        y1 = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('main', 'gui_do', (x1, y1), (width, height))
        # set grid layout properties
        set_grid_properties((x + 10, y + 45), 140, 20, 4)
        # add title label
        set_font('biggest')
        label = Label((0, 0), 'gui_do')
        set_font('normal')
        # create a rect for the frame for the display area
        frame = Rect(x, y, width, height)
        label.rect.x = frame.x + centre(frame.width, label.rect.width)
        label.rect.y = y
        self.gui.add_widget(label)
        # add buttons
        self.gui.add_widget(Button('Button_1', gridded(0, 0), 'Button'))
        self.gui.add_widget(Button('Button_2', gridded(0, 1), 'Button'))
        self.gui.add_widget(Button('Button_3', gridded(0, 2), 'Button'))
        # add in a pushbutton group
        self.pb1 = PushButtonGroup('B1', gridded(1, 0), 'Button Group 1', 'pb1', PushButtonKind.BOX)
        pb2 = PushButtonGroup('B2', gridded(1, 1), 'Button Group 2', 'pb1', PushButtonKind.BOX)
        pb3 = PushButtonGroup('B3', gridded(1, 2), 'Button Group 3', 'pb1', PushButtonKind.BOX)
        self.gui.add_widget(self.pb1)
        self.gui.add_widget(pb2)
        self.gui.add_widget(pb3)
        # add another column of pushbuttons
        self.pb4 = PushButtonGroup('R1', gridded(2, 0), 'Radio Group 1', 'pb2', PushButtonKind.RADIO)
        pb5 = PushButtonGroup('R2', gridded(2, 1), 'Radio Group 2', 'pb2', PushButtonKind.RADIO)
        pb6 = PushButtonGroup('R3', gridded(2, 2), 'Radio Group 3', 'pb2', PushButtonKind.RADIO)
        self.gui.add_widget(self.pb4)
        self.gui.add_widget(pb5)
        self.gui.add_widget(pb6)
        # create labels for groups
        self.label_button = Label(gridded(1, 3), 'N/A')
        self.label_radio = Label(gridded(2, 3), 'N/A')
        self.gui.add_widget(self.label_button)
        self.gui.add_widget(self.label_radio)
        # create a vertical scrollbar
        sb1 = Scrollbar('S1', Rect(frame.right - 30, y + 10, 20, frame.bottom - 20 - frame.y), False)
        sb1.set(100, 0, 30)
        # create a horizontal scrollbar
        sb2 = Scrollbar('S2', Rect(x + 10, y + height - 30, frame.right - 45 - frame.x, 20), True)
        sb2.set(100, 0, 30)
        # add the scrollbars in
        self.gui.add_widget(sb1)
        self.gui.add_widget(sb2)
        # end adding window widgets

        # gui setup done
        self.gui.set_active_object(None)

        # load an image to be used for a cursor
        self.cursor_image = image_alpha('cursors', 'Icons8_cursor.png')
        # read initial mouse position
        self.mouse_position = pygame.mouse.get_pos()
        # set a background image
        self.screen.blit(pygame.image.load(file_resource('images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 0
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # make the bigger font entry the default for new renders
        while self.running:
            # handle events
            self.handle_events()
            set_font('normal')
            self.label_button.set_label(f'Button: {self.pb1.read()}')
            self.label_radio.set_label(f'Radio: {self.pb4.read()}')
            set_last_font()
            # draw gui widgets
            self.gui.draw_gui()
            # draw mouse graphic
            mouse_rect = Rect(self.mouse_position[0] - 3, self.mouse_position[1], 16, 16)
            mouse_bitmap = copy_graphic_area(self.screen, mouse_rect)
            self.screen.blit(self.cursor_image, mouse_rect)
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undo mouse graphic draw
            self.screen.blit(mouse_bitmap, mouse_rect)
            # undraw gui widgets
            self.gui.undraw_gui()
        # release resources
        pygame.quit()

    def handle_events(self):
        # handle the pygame event queue
        for event in pygame.event.get():
            # if the mouse moves update the internal position
            if event.type == MOUSEMOTION:
                self.mouse_position = event.pos
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
