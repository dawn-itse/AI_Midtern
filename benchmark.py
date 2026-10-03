"""Compare the repository's UCS and A* implementations on Sokoban maps."""
import csv
import multiprocessing
import queue
import time
import tracemalloc
from pathlib import Path
from astar import astar_search
from heuristic import SokobanHeuristic
from sokoban_core import SokobanProblem
from ucs import uniform_cost_search
ROOT = Path(__file__).resolve().parent
MAP_DIRECTORY = ROOT / "maps"
RESULTS_FILE = ROOT / "results" / "benchmark.csv"
REPEATS = 3
WORKER_LIMIT_SECONDS = 5.0
A_STAR_LIMIT_SECONDS = 4.5

def _run_once(map_path, algorithm, result_queue):
    """Run one search in an isolated process and return its measured metrics."""
    try:
        problem = SokobanProblem(map_path)
        tracemalloc.start()
        started = time.perf_counter()
        if algorithm == "UCS":
            result, expanded, max_frontier, _ = uniform_cost_search(problem)
        else:
            heuristic = SokobanHeuristic(problem)
            result, expanded, max_frontier, _ = astar_search(
                problem, heuristic=heuristic, timeout_seconds=A_STAR_LIMIT_SECONDS
            )
        runtime = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result_queue.put({
            "found": result is not None,
            "cost": result[1] if result is not None else "",
            "expanded": expanded,
            "max_frontier": max_frontier,
            "runtime_seconds": runtime,
            "peak_memory_bytes": peak_bytes,
            "status": "solved" if result is not None else "no_solution",
            "error": "",
        })
    except BaseException as exc:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        result_queue.put({
            "found": False, "cost": "", "expanded": "", "max_frontier": "",
            "runtime_seconds": "", "peak_memory_bytes": "", "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        })


def _candidate_maps():
    """Select maps in maps/ that match SokobanProblem's A/B/D/C format."""
    selected = []
    for path in sorted(MAP_DIRECTORY.glob("*.txt")):
        try:
            problem = SokobanProblem(path)
            if problem.initial_state[0] is None:
                print(f"Skipping {path.relative_to(ROOT)}: no A agent marker")
                continue
            if len(problem.initial_state[1]) != len(problem.targets):
                print(f"Skipping {path.relative_to(ROOT)}: box/goal counts differ")
                continue
            selected.append(path)
        except Exception as exc:
            print(f"Skipping {path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
    return selected


def _measure(map_path, algorithm):
    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    process = context.Process(target=_run_once, args=(str(map_path), algorithm, result_queue))
    wall_started = time.perf_counter()
    process.start()
    process.join(WORKER_LIMIT_SECONDS)
    if process.is_alive():
        process.terminate()
        process.join()
        result_queue.close()
        return {
            "found": False, "cost": "", "expanded": "", "max_frontier": "",
            "runtime_seconds": time.perf_counter() - wall_started,
            "peak_memory_bytes": "", "status": "timeout",
            "error": f"worker exceeded {WORKER_LIMIT_SECONDS:.1f}s; UCS has no internal timeout check",
        }
    try:
        result = result_queue.get(timeout=1)
    except queue.Empty:
        result = {
            "found": False, "cost": "", "expanded": "", "max_frontier": "",
            "runtime_seconds": time.perf_counter() - wall_started,
            "peak_memory_bytes": "", "status": "error",
            "error": f"worker exited with code {process.exitcode} without metrics",
        }
    result_queue.close()
    return result

def _average(rows, field):
    values = [float(row[field]) for row in rows if row[field] not in ("", None)]
    return sum(values) / len(values) if values else None

def _display(value, digits=1):
    return f"{value:.{digits}f}" if value is not None else "-"

def main():
    maps = _candidate_maps()
    if not maps:
        print("No compatible maps found.")
        return

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "map", "algorithm", "run", "found", "cost", "expanded", "max_frontier",
        "runtime_seconds", "peak_memory_bytes", "status", "error",
    ]
    raw_rows = []
    for map_path in maps:
        map_name = map_path.relative_to(ROOT).as_posix()
        for algorithm in ("UCS", "A*"):
            for run_number in range(1, REPEATS + 1):
                metrics = _measure(map_path, algorithm)
                row = {"map": map_name, "algorithm": algorithm, "run": run_number, **metrics}
                raw_rows.append(row)
                print(
                    f"{map_name} | {algorithm} run {run_number}: {metrics['status']}"
                    + (f", cost={metrics['cost']}" if metrics["cost"] != "" else "")
                    + (f", time={float(metrics['runtime_seconds']):.3f}s"
                       if metrics["runtime_seconds"] != "" else "")
                )
    with RESULTS_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(raw_rows)

    print("\nAverage comparison (mean of completed runs; time in seconds, memory in MiB)")
    print(f"{'Map':<27} {'Algorithm':<10} {'Found':<8} {'Cost':<8} {'Expanded':<12} {'Time':<12} {'Peak MiB':<12}")
    for map_path in maps:
        map_name = map_path.relative_to(ROOT).as_posix()
        for algorithm in ("UCS", "A*"):
            rows = [r for r in raw_rows if r["map"] == map_name and r["algorithm"] == algorithm]
            runt = _average(rows, "runtime_seconds")
            mem = _average(rows, "peak_memory_bytes")
            expanded = _average(rows, "expanded")
            completed = [r for r in rows if r["status"] in ("solved", "no_solution")]
            found_count = sum(bool(r["found"]) for r in rows)
            costs = [str(r["cost"]) for r in completed if r["cost"] != ""]
            print(
                f"{map_name:<27} {algorithm:<10} {found_count}/{REPEATS:<6} "
                f"{','.join(sorted(set(costs))) or '-':<8} "
                f"{_display(expanded, 1):<12} "
                f"{_display(runt, 3):<12} "
                f"{_display(mem / (1024 * 1024) if mem is not None else None, 3):<12}"
            )
    print(f"\nRaw per-run results saved to {RESULTS_FILE.relative_to(ROOT).as_posix()}")
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
