import sys
import pygame
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, add, set_backdrop, set_font, set_cursor, restore_pristine
from gui import GKind, Label, Button
from gui import Scheduler

class Editor:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        # set window caption
        pygame.display.set_caption('Template')
        # create a gui manager
        fonts = (('titlebar', 'Ubuntu-B.ttf', 16), ('normal', 'Gimbot.ttf', 16), ('gui_do', 'Gimbot.ttf', 72))
        self.gui = gui_init(self.screen, fonts)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # main label
        set_font('gui_do')
        add(Label((50, 50),'gui_do'))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1040, 70, 30), 1, 'Exit'))
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # set running flag
        self.running = True
        # create a scheduler
        self.scheduler = Scheduler()

    def run(self):
        # launch scheduler
        self.scheduler.run_scheduler(self.preamble, self.handle_events, self.postamble)

    def preamble(self):
        # do pre-event handling code
        restore_pristine()

    def handle_events(self, event):
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

    def postamble(self):
        # do post-tasks code
        if not self.running:
            # release resources
            pygame.quit()
            # exit python
            sys.exit(0)

if __name__ == '__main__':
    Editor().run()
