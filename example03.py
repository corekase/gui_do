import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import set_surface, set_backdrop, centre, load_font, set_font, set_last_font
from gui import set_grid_properties, gridded, set_cursor, add, restore_pristine, window
from gui import GuiManager, GKind
from gui import Button, Image, ToggleButton, Label, Frame, FrState

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
        # create a gui manager
        self.gui = GuiManager()
        set_surface(self.screen)
        # blit a background image to the screen surface
        set_backdrop('watercolor-green-wallpaper-modified.jpg')
        # load fonts
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'), self.exit)
        self.window1_toggle = add(ToggleButton('toggle1', Rect(90, 1050, 170, 20), False, 'Window 1 Visible'))
        self.window2_toggle = add(ToggleButton('toggle2', Rect(270, 1050, 170, 20), False, 'Window 2 Visible'))
        # realize window
        _, _, screen_width, screen_height = self.screen.get_rect()
        window_width, window_height = 180, 205
        centre_x = centre(screen_width, window_width)
        centre_y = centre(screen_height, window_height)
        window('Realize', (centre_x, centre_y), (window_width, window_height))
        # add an image
        self.image = add(Image('image', Rect(15, 15, 145, 145), 'realize.png'))
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
        # number of boxes to draw on screen
        boxes = 200
        # setup a frame to draw on our surface
        size = 12
        frame = Frame('none', Rect(0, 0, size, size))
        frame.state = FrState.Armed
        # create our bitmap
        frame_bitmap = pygame.surface.Surface((size, size))
        # point the frame object at it
        frame.surface = frame_bitmap
        # and render onto that surface
        frame.draw()
        max_x, max_y = self.screen.get_rect().width - size, self.screen.get_rect().height - size
        areas = []
        for _ in range(boxes):
            x = randrange(0, self.screen.get_rect().width - size)
            y = randrange(0, self.screen.get_rect().height - size)
            dx = randrange(2, 7)
            dy = randrange(2, 7)
            if choice([True, False]):
                dx = -dx
            if choice([True, False]):
                dy = -dy
            areas.append((x, y, dx, dy))

        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            self.image.visible = self.toggle.read()
            self.toggle.visible = self.window1_toggle.read()
            new_areas = []
            for x, y, dx, dy in areas:
                x += dx
                y += dy
                if x < 0 or x > max_x:
                    dx = -dx
                if y < 0 or y > max_y:
                    dy = -dy
                self.screen.blit(frame_bitmap, (x, y))
                new_areas.append((x, y, dx, dy))
            #
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
            # undraw gui
            self.gui.undraw_gui()
            #
            for x, y, dx, dy in new_areas:
                area = Rect(x, y, size, size)
                # restore a bitmap area from the screen's pristine bitmap to the main surface
                restore_pristine(area)
            # swap the lists to start again
            areas = new_areas

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
