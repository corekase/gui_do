import time

class Timers:
    class Timer:
        def __init__(self, callback, duration):
            self.timer = 0.0
            self.previous_time = time.time()
            self.callback = callback
            self.duration = duration

    _instance_ = None

    def __new__(cls):
        if Timers._instance_ is None:
            Timers._instance_ = object.__new__(cls)
            Timers._instance_._populate_()
        return Timers._instance_

    def _populate_(self):
        self.timers = []

    def add_timer(self, callback, duration):
        timer = self.Timer(callback, duration)
        self.timers.append(timer)
        return timer

    def remove_timer(self, timer):
        if timer in self.timers:
            self.timers.remove(timer)

    def update(self):
        now_time = time.time()
        for obj in self.timers[:]:
            elapsed_time = now_time - obj.previous_time
            obj.previous_time = now_time
            obj.timer += elapsed_time
            if obj.timer >= obj.duration:
                obj.timer -= obj.duration
                if obj.callback != None:
                    obj.callback()
                else:
                    self.timers.remove(obj)
