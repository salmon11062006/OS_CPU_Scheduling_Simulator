from Helper import Task

def srtf_scheduler(tasks):
    time = 0
    remaining = tasks[:]
    current = None

    while remaining:
        available = [t for t in remaining if t.arrival_time <= time]

        if not available:
            time += 1
            continue

        # Always pick the task with the shortest *remaining* time
        current = min(available, key=lambda t: t.remaining_time)

        # Execute ONE unit (preemptive - re-evaluate after each tick)
        current.execute()
        time += 1

        # If task is completed, remove it from the list
        if current.completed:
            current.completion_time = time
            remaining.remove(current)
    
