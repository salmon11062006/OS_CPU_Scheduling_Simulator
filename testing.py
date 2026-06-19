from Helper import Task
from SJF import sjf_scheduler
from SRTF import srtf_scheduler

def make_tasks():
    """Recreate tasks fresh for each test since Task mutates state."""
    return [
        Task("P1", lambda: None, arrival_time=0, burst_time=6, priority=3),
        Task("P2", lambda: None, arrival_time=2, burst_time=4, priority=1),
        Task("P3", lambda: None, arrival_time=4, burst_time=2, priority=2),
        Task("P4", lambda: None, arrival_time=6, burst_time=1, priority=4),
    ]

def print_results(tasks, algorithm_name):
    print(f"\n{'='*40}")
    print(f"  {algorithm_name}")
    print(f"{'='*40}")
    print(f"{'Task':<8} {'Arrival':<10} {'Burst':<8} {'Finish':<10} {'TAT':<8} {'WT':<8}")
    print("-" * 40)

    total_tat, total_wt = 0, 0
    for t in sorted(tasks, key=lambda x: x.name):
        tat = t.turnaround_time()
        wt  = t.waiting_time()
        total_tat += tat
        total_wt  += wt
        print(f"{t.name:<8} {t.arrival_time:<10} {t.burst_time:<8} {t.completion_time:<10} {tat:<8} {wt:<8}")

    n = len(tasks)
    print("-" * 40)
    print(f"{'Avg':<8} {'':<10} {'':<8} {'':<10} {total_tat/n:<8.2f} {total_wt/n:<8.2f}")

def test_sjf():
    tasks = make_tasks()
    sjf_scheduler(tasks)
    print_results(tasks, "SJF")

def test_srtf():
    tasks = make_tasks()
    srtf_scheduler(tasks)
    print_results(tasks, "SRTF")

test_sjf()
test_srtf()