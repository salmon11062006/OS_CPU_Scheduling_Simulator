class Task:
    def __init__(self, name, func, arrival_time=0, burst_time=0, priority=0):
        self.name = name
        self.func = func
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority