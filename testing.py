from FCFS import fcfs
from Helper import Task
from MLQ import mlq
from RR import round_robin
from SJF import sjf
from SRTF import srtf
from nonPreEmptivePriority import nonPreEmptivePriority
from preEmptivePriority import preEmptivePriority

def make_tasks():
    """Recreate tasks fresh for each test since Task mutates state."""
    return [
        Task("P1", lambda: None, arrival_time=0, burst_time=6, priority=3, queue=0),
        Task("P2", lambda: None, arrival_time=2, burst_time=4, priority=1, queue=1),
        Task("P3", lambda: None, arrival_time=4, burst_time=2, priority=2, queue=0),
        Task("P4", lambda: None, arrival_time=6, burst_time=1, priority=4, queue=2),
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

def test_fcfs():
    tasks = make_tasks()
    fcfs(tasks)
    print_results(tasks, "FCFS")

def test_sjf():
    tasks = make_tasks()
    sjf(tasks)
    print_results(tasks, "SJF")

def test_rr():
    tasks = make_tasks()
    round_robin(tasks, quantum=2)
    print_results(tasks, "Round Robin (Quantum=2)")

def test_srtf():
    tasks = make_tasks()
    srtf(tasks)
    print_results(tasks, "SRTF")

def test_nonprepriority():
    tasks = make_tasks()
    nonPreEmptivePriority(tasks)
    print_results(tasks, "Non-Preemptive Priority")

def test_prepriority():
    tasks = make_tasks()
    preEmptivePriority(tasks)
    print_results(tasks, "Preemptive Priority")

def test_mlq():
    tasks = make_tasks()
    mlq(tasks, quantum=2)
    print_results(tasks, "Multi-Level Queue (Quantum=2)")

test_fcfs()
test_sjf()
test_srtf()
test_rr()
test_nonprepriority()
test_prepriority()
test_mlq()