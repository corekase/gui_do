import pygame
from random import randrange, choice
from pygame import Rect, FULLSCREEN, SCALED
from pygame.locals import K_ESCAPE
from gui import gui_init, set_backdrop, load_font, set_font, centre, colours
from gui import add, set_cursor, restore_pristine, Scrollbar, Window, set_buffered
from gui import GKind, Label, Button, Frame, FrState, Image, ToggleButton

class Demo:
    def __init__(self):
        # initialize pygame
        pygame.init()
        # create main window surface
        self.screen = pygame.display.set_mode((1920, 1080), FULLSCREEN | SCALED)
        self.screen_rect = self.screen.get_rect()
        # set window caption
        pygame.display.set_caption('gui_do')
        # hide system mouse pointer
        pygame.mouse.set_visible(False)
        # create a gui manager
        self.gui = gui_init(self.screen)
        # do not buffer the screen, for applications where the screen is wiped each cycle
        set_buffered(False)
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
        self.boxes_toggle = add(ToggleButton('boxes', Rect(90, 1050, 70, 20), True, 'Boxes'))
        self.circles_toggle = add(ToggleButton('circles', Rect(170, 1050, 70, 20), True, 'Circles'))
        # position of the window
        x, y, width, height = 0, 0, 320, 362
        window_x = centre(self.screen.get_rect().width, width)
        window_y = centre(self.screen.get_rect().height, height)
        # create the window and it adds itself to the gui_manager and makes itself the active object
        Window('Scrollbar Styles', (window_x, window_y), (width, height))
        x, y = 10, 10
        sb1 = add(Scrollbar('a', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 0))
        y += 22
        sb2 = add(Scrollbar('b', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 1))
        y += 22
        sb3 = add(Scrollbar('c', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 2))
        y += 22
        sb4 = add(Scrollbar('d', (100, 0, 30, 10), Rect(x, y, 300, 20), True, 3))
        y += 24
        sb5 = add(Scrollbar('e', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 0))
        x += 22
        sb6 = add(Scrollbar('f', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 1))
        x += 22
        sb7 = add(Scrollbar('g', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 2))
        x += 22
        sb8 = add(Scrollbar('h', (100, 0, 30, 10), Rect(x, y, 20, 250), False, 3))
        add(Image('realize', Rect(100, 100, 210, 210), 'realize.png', False))
        set_font('gui_do')
        add(Label((110, 310), 'Scrollbars!'))
        set_font('normal')
        # set cursor image
        set_cursor((1, 1), 'cursor.png')
        # set running flag
        self.running = True

    def run(self):
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()

        boxes = 50
        boxes_size = 12
        # get a list of positions
        boxes_position_list = self.make_position_list(boxes, boxes_size)
        # setup a frame to draw on our surface
        frame = Frame('none', Rect(0, 0, boxes_size, boxes_size))
        frame.state = FrState.Armed
        # create our bitmap
        frame_bitmap = pygame.surface.Surface((boxes_size, boxes_size))
        # point the frame object at it
        frame.surface = frame_bitmap
        # and render onto that surface
        frame.draw()
        # number of circles and their size to draw on screen
        circles = 50
        circles_size = 12
        # get a position list for them
        circles_position_list = self.make_position_list(circles, circles_size)
        from gui.bitmapfactory import BitmapFactory
        factory = BitmapFactory()
        circle_bitmap = factory.draw_radio_checked_bitmap(circles_size, colours['full'], colours['none'])

        # begin main loop
        while self.running:
            # handle events
            self.handle_events()
            # restore pristine bitmap for the screen
            restore_pristine()
            # update the toggle variables
            draw_boxes = self.boxes_toggle.read()
            draw_circles = self.circles_toggle.read()
            # handle events
            self.handle_events()
            # draw the boxes and circles if their respective toggles are true
            if draw_boxes:
                boxes_position_list = self.draw_update_position_list(boxes_position_list, boxes_size, frame_bitmap)
            if draw_circles:
                circles_position_list = self.draw_update_position_list(circles_position_list, circles_size, circle_bitmap)
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # tick to desired frame-rate
            clock.tick(fps)
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
                pass
            elif event.type == GKind.KeyDown:
                # handle key presses
                if event.key == K_ESCAPE:
                    # handle escape key
                    self.running = False

    def make_position_list(self, num_items, size):
        positions = []
        for _ in range(num_items):
            x = randrange(0, self.screen_rect.width - (size * 2))
            y = randrange(0, self.screen_rect.height - (size * 2))
            dx = randrange(2, 7)
            dy = randrange(2, 7)
            if choice([True, False]):
                dx = -dx
            if choice([True, False]):
                dy = -dy
            positions.append((x, y, dx, dy))
        return positions

    def draw_update_position_list(self, positions, size, bitmap):
        new_positions = []
        for x, y, dx, dy in positions:
            x += dx
            y += dy
            if x < 0 or x > self.screen_rect.width - size:
                dx = -dx
            if y < 0 or y > self.screen_rect.height - size:
                dy = -dy
            self.screen.blit(bitmap, (x, y))
            new_positions += [(x, y, dx, dy)]
        return new_positions

    # callbacks
    def exit(self):
        self.running = False

if __name__ == '__main__':
    Demo().run()
