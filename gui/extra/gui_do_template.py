# this is a template file to use as a starting point for your own applications,
# copy this template to your client folder and rename it to your application name
#
import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, set_backdrop, set_font, set_cursor, restore_pristine
from gui import GKind, Label, Button

class Template:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # set window caption
        pygame.display.set_caption('Template')
        # create a gui manager
        fonts = [['titlebar', 'Wiltype.ttf', 16],
                 ['normal', 'Gimbot.ttf', 16],
                 ['gui_do', 'Gimbot.ttf', 72]]
        self.gui = gui_init(self.screen, fonts)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # main label
        set_font('gui_do')
        add(Label((50, 50),'gui_do'))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1040, 70, 30), 'Exit'))
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
