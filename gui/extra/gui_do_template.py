# this is a template file to use as a starting point for your own applications,
# copy this template to your client folder and rename it to your application name
#
import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, set_backdrop, load_font, set_font
from gui import add, set_cursor, set_buffered, restore_pristine
from gui import GKind, Label, Button

class Template:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # set window caption
        pygame.display.set_caption('gui_do')
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        # create a gui manager
        self.gui = gui_init(self.screen)
        # don't save overdrawn bitmaps into a buffer automatically, and don't use undraw_gui()
        set_buffered(False)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # load font
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # main label
        set_font('gui_do')
        add(Label((50, 50),'gui_do'))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'))
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        while self.running:
            # restore the pristine area to the screen before drawing
            restore_pristine()
            # handle events
            self.handle_events()
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
        # release resources
        pygame.quit()

    def handle_events(self):
        # handle the gui event queue
        for event in self.gui.events():
            if event.type == GKind.Widget:
                if event.widget_id == 'exit':
                    # exit button clicked
                     self.running = False
            elif event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # escape key pressed
                    self.running = False
            elif event.type == GKind.Quit:
                # window close widget or alt-f4 keypress
                self.running = False

if __name__ == '__main__':
    Template().run()
