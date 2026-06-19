from Helper import Task

def fcfs_scheduler(tasks):
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


# Example usage
if __name__ == "__main__":
    def example_task():
        print("Executing task...")

    tasks = [
        Task(name="Task 1", func=example_task, arrival_time=0, burst_time=5),
        Task(name="Task 2", func=example_task, arrival_time=2, burst_time=3),
        Task(name="Task 3", func=example_task, arrival_time=4, burst_time=1)
    ]

    scheduled_tasks = fcfs_scheduler(tasks)

    for task in scheduled_tasks:
        print(f"{task.name}: Arrival Time={task.arrival_time}, Burst Time={task.burst_time}, Completion Time={task.completion_time}, Turnaround Time={task.turnaround_time()}, Waiting Time={task.waiting_time()}")