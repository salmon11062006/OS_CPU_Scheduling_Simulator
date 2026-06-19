from Helper import Task

def sjf_scheduler(tasks):
    time = 0 
    remaining = tasks[:] # copy so it does not mutate the original list

    while remaining:
        # only consider tasks that already arrived
        available = [t for t in remaining if t.arrival_time <= time]
        
        if not available:
            # No task ready yet - CPU id idle, jump to next arrival
            time = min(t.arrival_time for t in remaining)
            continue

        # Pick the task with the shortest burst time
        task = min(available, key=lambda t: t.burst_time)

        # Run it to completion (non-preemptive)
        while not task.completed:
            task.execute()
            time += 1
        
        task.completion_time = time
        remaining.remove(task)


