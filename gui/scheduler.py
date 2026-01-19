import time

class Timers:
    timers = {}

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
        self.tasks = {}
        self.preamble = None
        self.postamble = None

    class Task:
        def __init__(self, id, interval):
            self.id = id
            # times for yielding cooperative control
            self.time_start = 0.0
            self.time_duration = interval
            # pointer for a "receive information" method, takes one parameter (which can anything)
            # gives coroutine operations while only being a generator
            self.datagram = None

    def add_task(self, id, logic, interval, parameters=None, datagram = None):
        task = self.Task(id, interval)
        if parameters == None:
            task.task_logic = logic(id)
        else:
            task.task_logic = logic(id, parameters)
        if datagram != None:
            task.datagram = datagram
        self.tasks[id] = task

    def send_datagram(self, id, parameters):
        self.tasks[id].datagram(parameters)

    def remove_task(self, id):
        if id in self.tasks.keys():
            del self.tasks[id]

    def task_time(self, id):
        if (time.time() - self.tasks[id].time_start) >= self.tasks[id].time_duration:
            return True
        return False

    def task_match(self, *tasks):
        for task in tasks:
            if task in self.tasks.keys():
                return True
        return False

    def init_scheduler(self, preamble=None, postamble=None):
        if preamble == None:
            preamble = self.null
        if postamble == None:
            postamble = self.null
        self.preamble = preamble
        self.postamble = postamble

    def null(self):
        return

    def task_scheduler(self):
        if len(self.tasks) > 0:
            new_tasks = {}
            # call preamble
            self.preamble()
            for task in self.tasks.keys():
                # handle gui events
                pass
                # handle task logic
                try:
                    self.tasks[task].time_start = time.time()
                    next(self.tasks[task].task_logic)
                    new_tasks[task] = self.tasks[task]
                except StopIteration:
                    # task exited, and exception happened before the assignment into new_tasks
                    # so the task is dropped.
                    pass
            self.tasks = new_tasks
            # call postamble
            self.postamble()
            # draw gui
            pass
