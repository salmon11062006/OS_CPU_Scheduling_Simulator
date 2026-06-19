def fcfs(tasks):
    # Sort tasks by arrival time
    tasks.sort(key=lambda x: x.arrival_time)
    
    current_time = 0
    for task in tasks:
        # If the current time is less than the task's arrival time, move the current time to the task's arrival time
        if current_time < task.arrival_time:
            current_time = task.arrival_time
        
        # Execute the task until completion
        while not task.completed:
            task.execute()
            current_time += 1
        
        # Set the completion time for the task
        task.completion_time = current_time

    return tasks