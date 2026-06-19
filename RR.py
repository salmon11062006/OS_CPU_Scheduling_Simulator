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


def example_task():
    print("Executing task...")

tasks = [
    Task(name="Task 1", func=example_task, arrival_time=0, burst_time=5),
    Task(name="Task 2", func=example_task, arrival_time=2, burst_time=3),
    Task(name="Task 3", func=example_task, arrival_time=4, burst_time=1)
]

scheduled_tasks = round_robin(tasks, quantum=2)

for task in scheduled_tasks:
    print(f"{task.name}: Arrival Time={task.arrival_time}, Burst Time={task.burst_time}, Completion Time={task.completion_time}, Turnaround Time={task.turnaround_time()}, Waiting Time={task.waiting_time()}")
