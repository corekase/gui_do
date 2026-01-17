import time

class Scheduler:
    _instance_ = None

    def __new__(cls):
        if Scheduler._instance_ is None:
            Scheduler._instance_ = object.__new__(cls)
            Scheduler._instance_._populate_()
        return Scheduler._instance_

    def _populate_(self):
        self.timers = {}
        self.tasks = {}

    class Interval:
        def __init__(self, duration):
            self.timer = 0.0
            self.previous_time = time.time()
            self.duration = duration
            self.callback = None
            self.task = None

    def add_timer(self, id, duration, callback):
        self.timers[id] = self.Interval(duration)
        self.timers[id].callback = callback

    def remove_timer(self, id):
        if id in self.timers.keys():
            del self.timers[id]

    def timer_updates(self):
        now_time = time.time()
        for id in self.timers.keys():
            elapsed_time = now_time - self.timers[id].previous_time
            self.timers[id].previous_time = now_time
            self.timers[id].timer += elapsed_time
            if self.timers[id].timer >= self.timers[id].duration:
                self.timers[id].timer -= self.timers[id].duration
                self.timers[id].callback()

    def add_task(self, id, interval, task, params=None):
        self.tasks[id] = self.Interval(interval)
        if params == None:
            self.tasks[id].task = task(id)
        else:
            self.tasks[id].task = task(id, params)

    def remove_task(self, id):
        if id in self.tasks.keys():
            del self.tasks[id]

    def task_time(self, id):
        if id in self.tasks.keys():
            now_time = time.time()
            elapsed = now_time - self.tasks[id].previous_time
            self.tasks[id].previous_time = now_time
            self.tasks[id].timer += elapsed
            if self.tasks[id].timer >= self.tasks[id].duration:
                self.tasks[id].timer %= self.tasks[id].duration
                return True
        return False

    def task_match(self, *tasks):
        for task in tasks:
            if task in self.tasks.keys():
                return True
        return False

    def task_scheduler(self):
        if len(self.tasks) > 0:
            new_tasks = {}     
            for task in self.tasks.keys():
                try:
                    self.tasks[task].timer = 0.0
                    self.tasks[task].previous_time = time.time()
                    next(self.tasks[task].task)
                    new_tasks[task] = self.tasks[task]
                except StopIteration:
                    pass
            self.tasks = new_tasks
