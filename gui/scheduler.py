import time
import pygame
from enum import Enum

TKind = Enum('TKind', ['Finished'])

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
        self.gui = GuiManager()
        # queued and finished lists
        self.tasks_ready = []
        self.tasks_processed = []
        self.tasks_suspended = []

    class Task:
        def __init__(self, id, interval):
            self.id = id
            # times for yielding cooperative control
            self.time_start = 0.0
            self.time_duration = interval
            # pointer for a "receive information" method, takes one parameter (which can anything)
            # gives coroutine operations while only being a generator
            self.message_method = None

    def event(self, operation, item1=None):
        from .guimanager import GKind
        class TaskEvent:
            # an event object to be returned which includes pygame event information and gui_do information
            def __init__(self):
                # the event is a Task type
                self.type = GKind.Task
                # what the event represents
                self.operation = None
                # task id
                self.id = None
        task_event = TaskEvent()
        task_event.type = operation
        if operation == TKind.Finished:
            task_event.operation = TKind.Finished
            task_event.id = item1
        # elif more operations
        return task_event

    def add_task(self, id, logic, parameters=None, message_method=None):
        task = self.Task(id, 0.01)
        if parameters == None:
            task.task_logic = logic(id)
        else:
            task.task_logic = logic(id, parameters)
        task.message_method = message_method
        self.tasks[id] = task
        self.tasks_ready.append(id)

    def send_message(self, id, parameters):
        # send either a single value or a collection like a tuple or list to the method id
        self.tasks[id].message_method(parameters)

    def remove_tasks(self, *tasks):
        for id in tasks:
            if id in self.tasks_ready:
                self.tasks_ready.pop(self.tasks_ready.index(id))
                del self.tasks[id]
            if id in self.tasks_processed:
                self.tasks_processed.pop(self.tasks_processed.index(id))
                del self.tasks[id]

    def suspend_tasks(self, *tasks):
        for id in tasks:
            # move id to suspended list from either the queued or finished lists
            if id in self.tasks_ready:
                self.tasks_suspended.append(self.tasks_ready.pop(self.tasks_ready.index(id)))
            elif id in self.tasks_processed:
                self.tasks_suspended.append(self.tasks_processed.pop(self.tasks_processed.index(id)))

    def resume_tasks(self, *tasks):
        for id in tasks:
            # move id from suspended list to end of queued list
            if id in self.tasks_suspended:
                self.tasks_ready.append(self.tasks_suspended.pop(self.tasks_suspended.index(id)))

    def read_suspended(self):
        # return a list of suspended task id's
        return self.tasks_suspended

    def read_suspended_len(self):
        # return the number of suspended tasks
        return len(self.tasks_suspended)

    def task_time(self, id):
        if (time.time() - self.tasks[id].time_start) >= self.tasks[id].time_duration:
            return True
        return False

    def tasks_active(self):
        if (len(self.tasks_ready) > 0) or (len(self.tasks_processed) > 0):
            return True
        return False

    def tasks_active_match_any(self, *tasks):
        # if a task is in either tasks_ready or tasks_processed then return True
        for task in tasks:
            if task in self.tasks_ready:
                return True
            elif task in self.tasks_processed:
                return True
        return False

    def tasks_active_match_all(self, *tasks):
        pass

    def null(self):
        return

    def run_scheduler(self, preamble=None, event_handler=None, postamble=None):
        def task_process():
            # separate out duplicate code so that waiting processed list id's don't miss a cycle when the ready list is empty
            try:
                task_id = self.tasks_ready.pop(0)
                self.tasks[task_id].time_start = time.time()
                next(self.tasks[task_id].task_logic)
                self.tasks_processed.append(task_id)
            except StopIteration:
                # task exited, and exception from next() happened before appending the id to the processed list
                self.tasks_finished.append(task_id)
        if event_handler == None:
            event_handler = self.null
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
            # send gui events
            for event in self.gui.events():
                event_handler(event)
            # handle task logic
            self.tasks_finished = []
            if len(self.tasks_ready) > 0:
                task_process()
            elif len(self.tasks_ready) == 0:
                self.tasks_ready = self.tasks_processed
                if len(self.tasks_processed) > 0:
                    self.tasks_processed.clear()
                if len(self.tasks_ready) > 0:
                    # do process here again because ready list was empty
                    task_process()
            # send task events
            for id in self.tasks_finished:
                event_handler(self.event(TKind.Finished, id))
            self.tasks_finished.clear()
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
