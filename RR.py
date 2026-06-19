from collections import deque
from Helper import Task

def round_robin(tasks, quantum=2):
    tasks.sort(key=lambda x: x.arrival_time)
    current_time = 0
    queue = deque()
    not_arrived = list(tasks)

    while not_arrived and not_arrived[0].arrival_time <= current_time:
        queue.append(not_arrived.pop(0))

    while queue:
        task = queue.popleft()
        
        if current_time < task.arrival_time:
            current_time = task.arrival_time
        
        time_slice = min(quantum, task.remaining_time)
        for i in range(time_slice):
            task.execute()
            current_time += 1
            while not_arrived and not_arrived[0].arrival_time <= current_time:
                queue.append(not_arrived.pop(0))

        if task.completed:
            task.completion_time = current_time
        else:
            queue.append(task)

    return tasks