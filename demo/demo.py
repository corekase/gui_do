import pygame
from pygame import Rect, FULLSCREEN, SCALED, QUIT
from pygame.locals import MOUSEMOTION, KEYDOWN, K_ESCAPE
from gui import GuiManager, PushButtonKind
from gui import Frame, Label, Button, PushButtonGroup, Scrollbar
from gui import file_resource, image_alpha, cut, centre, set_font, gprint
from gui import set_width, set_height, set_spacing, set_anchor, gridded

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
        # create a gui manager
        self.gui_manager = GuiManager(self.screen)
        # dimensions of the main frame for gui objects
        width = 500
        height = 200
        # name of the context
        main = 'main'
        # get centred pixel coordinates for that
        x = centre(self.screen.get_rect().width, width)
        y = centre(self.screen.get_rect().height, height)
        # origin for gprint's
        self.x, self.y = x, y
        # set width of rect areas
        set_width(140)
        # set height of rect areas
        set_height(20)
        # spacing between rect areas
        set_spacing(4)
        # origin of rect areas
        set_anchor((x + 10, y + 45))
        # create a frame for the display area
        frame = Rect(x, y, width, height)
        # create and add a frame to the main context
        self.gui_manager.add_widget(main, Frame('frame', frame))
        # and a label
        set_font('biggest')
        label = Label((0, 0), 'gui_do')
        set_font('normal')
        label.rect.x = frame.x + centre(frame.width, label.rect.width)
        label.rect.y = y
        self.gui_manager.add_widget(main, label)
        # add buttons
        self.gui_manager.add_widget(main, Button('Button_1', gridded(0, 0), 'Exit'))
        self.gui_manager.add_widget(main, Button('Button_2', gridded(0, 1), 'Button'))
        self.gui_manager.add_widget(main, Button('Button_3', gridded(0, 2), 'Button'))
        # add in a pushbutton group
        self.pb1 = PushButtonGroup('B1', gridded(1, 0), 'Button Group 1', 'pb1', PushButtonKind.BOX)
        pb2 = PushButtonGroup('B2', gridded(1, 1), 'Button Group 2', 'pb1', PushButtonKind.BOX)
        pb3 = PushButtonGroup('B3', gridded(1, 2), 'Button Group 3', 'pb1', PushButtonKind.BOX)
        self.gui_manager.add_widget(main, self.pb1)
        self.gui_manager.add_widget(main, pb2)
        self.gui_manager.add_widget(main, pb3)
        # add another column of pushbuttons
        self.pb4 = PushButtonGroup('R1', gridded(2, 0), 'Radio Group 1', 'pb2', PushButtonKind.RADIO)
        pb5 = PushButtonGroup('R2', gridded(2, 1), 'Radio Group 2', 'pb2', PushButtonKind.RADIO)
        pb6 = PushButtonGroup('R3', gridded(2, 2), 'Radio Group 3', 'pb2', PushButtonKind.RADIO)
        self.gui_manager.add_widget(main, self.pb4)
        self.gui_manager.add_widget(main, pb5)
        self.gui_manager.add_widget(main, pb6)
        # create a vertical scrollbar
        sb1 = Scrollbar('S1', Rect(frame.right - 30, y + 10, 20, frame.bottom - 20 - frame.y), False)
        sb1.set(100, 0, 30)
        # create a horizontal scrollbar
        sb2 = Scrollbar('S2', Rect(x + 10, y + height - 30, frame.right - 50 - frame.x, 20), True)
        sb2.set(100, 0, 30)
        # add the scrollbars in
        self.gui_manager.add_widget(main, sb1)
        self.gui_manager.add_widget(main, sb2)
        # switch to the 'main' context
        self.gui_manager.switch_context(main)
        # load an image to be used for a cursor
        self.cursor_image = image_alpha('cursors', 'Icons8_cursor.png')
        # read initial mouse position
        self.mouse_position = pygame.mouse.get_pos()
        # set a background image
        self.screen.blit(pygame.image.load(file_resource('images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # draw an outline frame
        x, y, w, h = frame
        outline = Frame('None', Rect(x - 10, y - 10, w + 20, h + 20))
        outline.surface = self.screen
        outline.draw()
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 0
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # make the bigger font entry the default for new renders
        set_font('normal')
        while self.running:
            # handle events
            self.handle_events()
            # draw gui widgets
            self.gui_manager.draw_widgets()
            # draw current pushbutton
            gprint(self.screen, f'Button group: {self.pb1.read()}', (self.x + 10, self.y + 120))
            gprint(self.screen, f'Radio group: {self.pb4.read()}', (self.x + 10, self.y + 135))
            # draw mouse graphic
            mouse_rect = Rect(self.mouse_position[0] - 3, self.mouse_position[1], 16, 16)
            mouse_bitmap = cut(self.screen, mouse_rect)
            self.screen.blit(self.cursor_image, mouse_rect)
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undo mouse graphic draw
            self.screen.blit(mouse_bitmap, mouse_rect)
            # undraw gui widgets
            self.gui_manager.undraw_widgets()
        # release resources
        pygame.quit()

    def handle_events(self):
        # handle the pygame event queue
        for event in pygame.event.get():
            # if the mouse moves update the internal position
            if event.type == MOUSEMOTION:
                self.mouse_position = event.pos
            # check if any gui objects handle the event
            gui_event = self.gui_manager.handle_event(event)
            # if gui_event isn't None then it is a gui event
            if gui_event != None:
                # handle gui events
                if gui_event == 'Button_1':
                    # Button_1 was clicked
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
