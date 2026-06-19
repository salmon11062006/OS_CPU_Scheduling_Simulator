from Helper import Task

def preEmptivePriority(tasks):
    tasks.sort(key=lambda x: x.arrival_time)
    current_time = 0
    completed_tasks = 0
    n = len(tasks)

    while completed_tasks < n:
        available_tasks = [task for task in tasks if task.arrival_time <= current_time and not task.completed]

        if not available_tasks:
            current_time = min(task.arrival_time for task in tasks if not task.completed)
            continue

        task = max(available_tasks, key=lambda x: x.priority)

        while not task.completed:
            task.execute()
            current_time += 1

        task.completion_time = current_time
        completed_tasks += 1

    return tasks

def example_task():
    print("Executing task...")

tasks = [
    Task(name="Task 1", func=example_task, arrival_time=0, burst_time=5, priority=1),
    Task(name="Task 2", func=example_task, arrival_time=2, burst_time=3, priority=2),
    Task(name="Task 3", func=example_task, arrival_time=4, burst_time=1, priority=3)
]

scheduled_tasks = preEmptivePriority(tasks)

for task in scheduled_tasks:
    print(f"{task.name}: Arrival Time={task.arrival_time}, Burst Time={task.burst_time}, Completion Time={task.completion_time}, Turnaround Time={task.turnaround_time()}, Waiting Time={task.waiting_time()}")
