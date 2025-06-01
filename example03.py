import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import set_surface, file_resource, centre, load_font, set_font, set_last_font
from gui import set_grid_properties, gridded, set_cursor, add
from gui import GuiManager, GKind, Window
from gui import Button, Image, ToggleButton, Label

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
        # blit a background image to the screen surface
        self.screen.blit(pygame.image.load(file_resource('images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
        # create a gui manager
        self.gui = GuiManager()
        set_surface(self.screen)
        # load fonts
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # add a title label to the screen
        set_font('gui_do')
        add(Label((50, 20), 'gui_do'))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'), self.exit)
        # realize window
        window_x, window_y, width, height = 50, 110, 180, 205
        Window('Realize', (window_x, window_y), (width, height))
        # add an image
        add(Image('image', Rect(15, 15, 145, 145), 'realize.png'))
        # add a toggle button
        self.toggle = add(ToggleButton('toggle', Rect(15, 170, 145, 20), True, 'On', 'Off'))
        # set cursor image
        set_cursor((1, 1), 'Icons8_cursor.png')
        # set running flag
        self.running = True

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
            # draw gui
            self.gui.draw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undraw gui
            self.gui.undraw_gui()
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
                pass
            elif event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # handle escape key
                    self.running = False

    # callbacks
    def exit(self):
        self.running = False

if __name__ == '__main__':
    Demo().run()
