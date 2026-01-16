import time

class Scheduler:
    class Timer:
        def __init__(self, callback, duration):
            self.timer = 0.0
            self.previous_time = time.time()
            self.callback = callback
            self.duration = duration

    class Task:
        def __init__(self, duration):
            self.timer = 0.0
            self.previous_time = time.time()
            self.duration = duration

    _instance_ = None
    def __new__(cls):
        if Scheduler._instance_ is None:
            Scheduler._instance_ = object.__new__(cls)
            Scheduler._instance_._populate_()
        return Scheduler._instance_

    def _populate_(self):
        self.timers = []
        self.task_timers = {}
        self.tasks = []

    def add_timer(self, callback, duration):
        timer = self.Timer(callback, duration)
        self.timers.append(timer)
        return timer

    def remove_timer(self, timer):
        if timer in self.timers:
            self.timers.remove(timer)

    def update_timer(self):
        now_time = time.time()
        for obj in self.timers[:]:
            elapsed_time = now_time - obj.previous_time
            obj.previous_time = now_time
            obj.timer += elapsed_time
            if obj.timer >= obj.duration:
                obj.timer -= obj.duration
                obj.callback()

    def add_task(self, id, interval, task, params=None):
        t1 = task(id, params)
        self.task_timers[id] = self.Task(interval)
        self.tasks.append((id, t1))

    def remove_task(self, id):
        if id in self.task_timers.keys():
            del self.task_timers[id]

    def poll_task_time(self, id):
        if id in self.task_timers.keys():
            now_time = time.time()
            time_slice = self.task_timers[id]
            elapsed = now_time - time_slice.previous_time
            time_slice.previous_time = now_time
            time_slice.timer += elapsed
            if time_slice.timer >= time_slice.duration:
                time_slice.timer -= time_slice.duration
                return True
        return False

    def task_scheduler(self):
        if len(self.tasks) > 0:
            new_tasks = []     
            for id, task in self.tasks:
                try:
                    next(task)
                    new_tasks.append((id, task))
                except StopIteration:
                    self.remove_task(id)
            self.tasks = new_tasks
