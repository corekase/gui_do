import os
import pygame
from pygame import Rect, FULLSCREEN, SCALED, QUIT
from pygame.locals import MOUSEMOTION, KEYDOWN, K_ESCAPE
from gui import GuiManager, Frame, Label, Button
from gui.utility import image_alpha, cut, file_resource, centre

if os.name == 'nt':
    # fixes graphical scaling issues with Windows
    # to reproduce issue: run on a 4k display with the screen resolution being 1920x1080
    # with FULLSCREEN and SCALED flags and Windows OS system scaling set to 150%
    # without setting DPIAware below
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()

class Main:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface, if not using vsync adjust fps in run()
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED, vsync=1)
        # set window caption
        pygame.display.set_caption('Test')
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        # create a gui manager
        self.gui_manager = GuiManager(self.screen)
        # dimensions of the main frame for gui objects
        width = 200
        height = 110
        # get centred pixel coordinates for that
        x = centre(self.screen.get_rect().width, width)
        y = centre(self.screen.get_rect().height, height)
        # create a rect for those values
        frame = Rect(x, y, width, height)
        # create and add a frame to the menu context
        self.gui_manager.add_widget('menu', Frame('frame', frame))
        # and a label
        label = Label((0, 0), 'gui_do Demo!')
        label.rect.x = frame.x + centre(frame.width, label.rect.width)
        label.rect.y = y + 11
        self.gui_manager.add_widget('menu', label)
        # a button
        self.gui_manager.add_widget('menu', Button('Button_1',
                        Rect(x + 10, y + 45, width - 20, 20), 'button one'))
        # and another button
        self.gui_manager.add_widget('menu', Button('Button_2',
                        Rect(x + 10, y + 70, width - 20, 20), 'button two'))
        # switch to the 'menu' context
        self.gui_manager.switch_context('menu')
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

        while self.running:
            # handle events
            self.handle_events()
            # draw gui widgets
            self.gui_manager.draw_widgets()
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
                    pass
                elif gui_event == 'Button_2':
                    # Button_2 was clicked
                    pass
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
