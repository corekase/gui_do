import time
import pygame

class Timers:
    _instance_ = None
    timers = {}

    def __new__(cls):
        if Timers._instance_ is None:
            Timers._instance_ = object.__new__(cls)
            Timers._instance_._populate_()
        return Timers._instance_

    def _populate_(self):
        pass

    class Interval:
        def __init__(self, duration):
            self.timer = 0.0
            self.previous_time = time.time()
            self.duration = duration
            self.callback = None

    def add_timer(self, id, duration, callback):
        Timers.timers[id] = self.Interval(duration)
        Timers.timers[id].callback = callback

    def remove_timer(self, id):
        if id in Timers.timers.keys():
            del Timers.timers[id]

    def timer_updates(self):
        now_time = time.time()
        for id in Timers.timers.keys():
            elapsed_time = now_time - Timers.timers[id].previous_time
            Timers.timers[id].previous_time = now_time
            Timers.timers[id].timer += elapsed_time
            if Timers.timers[id].timer >= Timers.timers[id].duration:
                Timers.timers[id].timer -= Timers.timers[id].duration
                Timers.timers[id].callback()

class Scheduler:
    _instance_ = None

    def __new__(cls):
        if Scheduler._instance_ is None:
            Scheduler._instance_ = object.__new__(cls)
            Scheduler._instance_._populate_()
        return Scheduler._instance_

    def _populate_(self):
        from .guimanager import GuiManager
        self.tasks = {}
        self.preamble = None
        self.postamble = None
        self.gui = GuiManager()
        # queued and finished lists
        self.queued = []
        self.finished = []

    class Task:
        def __init__(self, id, interval):
            self.id = id
            # times for yielding cooperative control
            self.time_start = 0.0
            self.time_duration = interval
            # pointer for a "receive information" method, takes one parameter (which can anything)
            # gives coroutine operations while only being a generator
            self.datagram = None

    def add_task(self, id, logic, parameters=None, datagram = None):
        task = self.Task(id, 0.01)
        if parameters == None:
            task.task_logic = logic(id)
        else:
            task.task_logic = logic(id, parameters)
        task.datagram = datagram
        self.tasks[id] = task
        self.queued.append(id)

    def send_datagram(self, id, parameters):
        self.tasks[id].datagram(parameters)

    def remove_tasks(self, *tasks):
        for id in tasks:
            if id in self.queued:
                self.queued.pop(self.queued.index(id))
                del self.tasks[id]
            if id in self.finished:
                self.finished.pop(self.finished.index(id))
                del self.tasks[id]

    def task_time(self, id):
        if (time.time() - self.tasks[id].time_start) >= self.tasks[id].time_duration:
            return True
        return False

    def active_tasks(self):
        if len(self.queued) >0 or len(self.finished) > 0:
            return True
        return False

    def task_match(self, *tasks):
        for task in tasks:
            if task in self.queued:
                return True
        return False

    def null(self):
        return

    def run_scheduler(self, preamble=None, handler=None, postamble=None):
        if handler == None:
            handler = self.null
        if preamble == None:
            preamble = self.null
        if postamble == None:
            postamble = self.null
        # fps to maintain, if 0 then unlimited
        fps = 60
        # a pygame clock to control the fps
        clock = pygame.time.Clock()
        while True:
            # call preamble
            preamble()
            # handle gui events
            handler()
            # handle task logic
            if len(self.queued) > 0:
                try:
                    task = self.queued.pop(0)
                    self.tasks[task].time_start = time.time()
                    next(self.tasks[task].task_logic)
                    self.finished.append(task)
                except StopIteration:
                    # task exited, and exception from next() happened before appending the id to the finished list
                    pass
            else:
                self.queued = self.finished
                self.finished.clear()
            # call postamble
            postamble()
            # draw gui
            self.gui.draw_gui()
            # buffer to the screen
            pygame.display.flip()
            # undo changes after flip if buffering
            if self.gui.buffered:
                self.gui.undraw_gui()
            # tick to desired frame-rate
            clock.tick(fps)
