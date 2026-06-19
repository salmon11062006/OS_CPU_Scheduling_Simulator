from collections import deque

def mlq(tasks, quantum=2):
    tasks.sort(key=lambda x: x.arrival_time)
    not_arrived = list(tasks)
    queue0 = deque()  # highest priority - Round Robin
    queue1 = deque()  # lower priority - FCFS

    current_time = 0
    completed_tasks = 0
    n = len(tasks)

    def admit_arrivals():
        while not_arrived and not_arrived[0].arrival_time <= current_time:
            arrived_task = not_arrived.pop(0)
            if arrived_task.queue == 0:
                queue0.append(arrived_task)
            else:
                queue1.append(arrived_task)

    admit_arrivals()

    while completed_tasks < n:
        admit_arrivals()

        if queue0:
            # ---- Round Robin within queue 0 ----
            task = queue0.popleft()
            time_slice = min(quantum, task.remaining_time)
            for _ in range(time_slice):
                task.execute()
                current_time += 1
                admit_arrivals()

            if task.completed:
                task.completion_time = current_time
                completed_tasks += 1
            else:
                queue0.append(task)  # back of queue 0

        elif queue1:
            # ---- FCFS within queue 1, preemptible by queue 0 ----
            task = queue1.popleft()
            while not task.completed:
                task.execute()
                current_time += 1
                admit_arrivals()
                if queue0:  # higher-priority task arrived - preempt
                    break

            if task.completed:
                task.completion_time = current_time
                completed_tasks += 1
            else:
                queue1.appendleft(task)  # keep its place, resumes first when queue 1 runs again

        else:
            # nothing available yet - jump to next arrival
            current_time = not_arrived[0].arrival_time
            admit_arrivals()

    return tasks