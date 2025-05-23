import pygame
from pygame import Rect, FULLSCREEN, SCALED, QUIT
from pygame.locals import MOUSEMOTION, KEYDOWN, K_ESCAPE
from gui import GuiManager, Frame, Label, Button, PushButtonGroup, Scrollbar
from gui import file_resource, image_alpha, cut, centre, render_text, set_font

class Main:
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
        width = 260
        height = 200
        button_width = 100
        button_height = 20
        # name of the context
        main = 'main'
        # get centred pixel coordinates for that
        x = centre(self.screen.get_rect().width, width)
        y = centre(self.screen.get_rect().height, height)
        self.x, self.y = x, y
        # create a rect for those values
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
        self.gui_manager.add_widget(main, Button('Button_1',
                        Rect(x + 10, y + 45, button_width, button_height), 'Exit'))
        self.gui_manager.add_widget(main, Button('Button_2',
                        Rect(x + 10, y + 70, button_width, button_height), 'Button'))
        self.gui_manager.add_widget(main, Button('Button_3',
                        Rect(x + 10, y + 95, button_width, button_height), 'Button'))
        # add in a pushbutton group
        self.pb1 = PushButtonGroup('One', Rect(x + button_width + 20, y + 45, button_width, button_height), 'One', 'pb1')
        pb2 = PushButtonGroup('Two', Rect(x + button_width + 20, y + 70, button_width, button_height), 'Two', 'pb1')
        pb3 = PushButtonGroup('Three', Rect(x + button_width + 20, y + 95, button_width, button_height), 'Three', 'pb1')
        self.gui_manager.add_widget(main, self.pb1)
        self.gui_manager.add_widget(main, pb2)
        self.gui_manager.add_widget(main, pb3)
        # create a vertical scrollbar
        sb1 = Scrollbar('S1', Rect(x + (button_width * 2) + 30, y + 45, 20, 140), False)
        sb1.set(100, 0, 30)
        # create a horizontal scrollbar
        sb2 = Scrollbar('S2', Rect(x + 10, y + height - 35, 210, 20), True)
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
        set_font('bigger')
        while self.running:
            # handle events
            self.handle_events()
            # draw gui widgets
            self.gui_manager.draw_widgets()
            # draw current pushbutton
            bitmap = render_text(f'Selected: {self.pb1.read()}')
            self.screen.blit(bitmap, (self.x + 10, self.y + 120))
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

if __name__ == '__main__':
    # Launch program
    Main().run()
