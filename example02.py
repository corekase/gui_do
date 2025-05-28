import pygame
from pygame import FULLSCREEN, SCALED, QUIT
from pygame import Rect
from gui import GuiManager
from gui import load_font, set_save, set_font, add, set_cursor, file_resource
from gui import Button

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
        # load fonts
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        # manipulator to control whether a screen widget saves the graphic underneath it
        set_save(False)
        # manipulator to set one of the loaded font names
        set_font('normal')
        add(Button('exit', Rect(10, 1050, 140, 20), 'Exit'), self.exit)
        # set cursor image
        set_cursor((4, 0), 'cursors', 'Icons8_cursor.png')
        # set a background image
        self.screen.blit(pygame.image.load(file_resource('images', 'watercolor-green-wallpaper-modified.jpg')).convert(), (0, 0))
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

            # draw gui
            self.gui.draw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
            # buffer to the screen
            pygame.display.flip()
            # undraw gui
            self.gui.undraw_gui()

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
