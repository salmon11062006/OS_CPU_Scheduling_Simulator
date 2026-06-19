def nonPreEmptivePriority(tasks):
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