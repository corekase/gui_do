# this is a template file to use as a starting point for your own applications,
# copy this template to your client folder and rename it to your application name
#
import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, set_backdrop, load_font, set_font, centre
from gui import add, set_cursor, restore_pristine, Window
from gui import GKind, Label, Button, Frame, FrState, Canvas

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
        self.gui_do_label = add(Label((50, 50),'gui_do', False))
        set_font('normal')
        # exit button, uses a callback function
        add(Button('exit', Rect(10, 1050, 70, 20), 'Exit'), self.exit)
        # position of the window
        width, height = 650, 450
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        Window('Canvas', (window_x, window_y), (width, height))
        self.canvas = add(Canvas('canvas', Rect(10, 10, 430, 430)))
        self.coordinate_label = add(Label(Rect(450, 10, 100, 20), 'N/A'))
        self.buttons_label = add(Label(Rect(450, 30, 100, 20), 'N/A'))
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        # whether to draw the boxes
        draw_boxes = True
        if draw_boxes:
            # number of boxes to draw on screen
            boxes = 50
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
            canvas_surface = self.canvas.get_canvas_surface()
            canvas_rect = canvas_surface.get_rect()
            max_x, max_y = canvas_rect.width - size, canvas_rect.height - size
            areas = []
            for _ in range(boxes):
                x = randrange(0, canvas_rect.width - size)
                y = randrange(0, canvas_rect.height - size)
                dx = randrange(2, 7)
                dy = randrange(2, 7)
                if choice([True, False]):
                    dx = -dx
                if choice([True, False]):
                    dy = -dy
                areas.append((x, y, dx, dy))

        # begin main loop
        while self.running:
            restore_pristine(self.gui_do_label.rect)
            # handle events
            self.handle_events()
            if draw_boxes:
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
                    canvas_surface.blit(frame_bitmap, (x, y))
                    new_areas += [(x, y, dx, dy)]
                areas = new_areas

            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
            # undraw gui
            self.gui.undraw_gui()

            if draw_boxes:
                #
                # undraw boxes
                #
                self.canvas.restore()

        # release resources
        pygame.quit()

    def handle_events(self):
        self.gui.timers.update()
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
                if event.widget_id == 'canvas':
                    x, y, buttons = self.canvas.read()
                    self.coordinate_label.set_label(f'X: {x}, Y: {y}')
                    self.buttons_label.set_label(f'{buttons}')
                else:
                    self.coordinate_label.set_label(f'N/A')
                    self.buttons_label.set_label(f'N/A')
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
