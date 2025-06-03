import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, set_backdrop, centre, load_font, set_font
from gui import set_cursor, add, restore_pristine, window
from gui import GKind
from gui import Label, Button, Image, ToggleButton, Frame, FrState, Scrollbar

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
        self.gui = gui_init(self.screen)
        # blit a background image to the screen surface
        set_backdrop('backdrop.jpg')
        # load fonts
        load_font('titlebar', 'Ubuntu-Medium.ttf', 10)
        load_font('normal', 'Ubuntu-Medium.ttf', 14)
        load_font('gui_do', 'Ubuntu-Medium.ttf', 36)
        # main label
        set_font('gui_do')
        self.gui_do_label = add(Label((50, 50),'gui_do'))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'), self.exit)
        # screen toggle buttons
        add(ToggleButton('WindowVisibleToggleButton', Rect(90, 1050, 170, 20), True, 'Window Visible'))
        add(ToggleButton('ToggleToggleButton', Rect(270, 1050, 170, 20), True, 'Togglebutton Visible'))
        add(ToggleButton('HorScrollToggleButton', Rect(450, 1050, 170, 20), True, 'Hor Scrollbar Visible'))
        add(ToggleButton('VerScrollToggleButton', Rect(630, 1050, 170, 20), True, 'Ver Scrollbar Visible'))
        # realize window
        _, _, screen_width, screen_height = self.screen.get_rect()
        window_width, window_height = 200, 225
        centre_x = centre(screen_width, window_width)
        centre_y = centre(screen_height, window_height)
        self.win = window('Example 03 Visibility Demo', (centre_x, centre_y), (window_width, window_height), 'example03_clipart.jpg')
        # add an image
        self.image_toggle = add(Image('image', Rect(15, 15, 145, 145), 'realize.png'))
        # add a toggle button
        self.image_toggle_button = add(ToggleButton('ImageToggleButton', Rect(10, 170, 150, 20), True, 'Image Visible'))
        # horizontal scrollbar
        self.sb1 = add(Scrollbar('hor_scroll', Rect(10, 195, 150, 20), True))
        self.sb1.set(100, 0, 30)
        # vertical scrollbar
        self.sb2 = add(Scrollbar('ver_scroll', Rect(170, 10, 20, 205), False))
        self.sb2.set(100, 0, 30)
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
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
            # restore pristine bitmap under the label rect
            restore_pristine(self.gui_do_label.get_rect())
            #
            # draw boxes
            #
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

            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
            # undraw gui
            self.gui.undraw_gui()

            #
            # undraw boxes
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
                if event.widget_id == 'WindowVisibleToggleButton':
                    self.win.set_visible(not self.win.get_visible())
                elif event.widget_id == 'ToggleToggleButton':
                    self.image_toggle_button.set_visible(not self.image_toggle_button.get_visible())
                elif event.widget_id == 'HorScrollToggleButton':
                    self.sb1.set_visible(not self.sb1.get_visible())
                elif event.widget_id == 'VerScrollToggleButton':
                    self.sb2.set_visible(not self.sb2.get_visible())
                elif event.widget_id == 'ImageToggleButton':
                    self.image_toggle.set_visible(not self.image_toggle.get_visible())
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
