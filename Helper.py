class Task:
    def __init__(self, name, func, arrival_time=0, burst_time=0, priority=0, queue=0):
        self.name = name
        self.func = func
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.queue = queue
        self.completed = False
        self.completion_time = None

    def execute(self):
        if self.remaining_time > 0:
            self.func()
            self.remaining_time -= 1
        if self.remaining_time == 0:
            self.completed = True
    
    def turnaround_time(self):
        if not self.completed:
            raise Exception("Task not Completed")
        if self.completion_time is None:
            raise Exception("Completion Time is None")
        return self.completion_time - self.arrival_time

    def waiting_time(self):
        if not self.completed:
            raise Exception("Task not Completed")
        if self.completion_time is None:
            raise Exception("Completion Time is None")
        return self.turnaround_time() - self.burst_time
