"""Measure baseline vs coverage-instrumented execution time.

Runs workload.run() repeatedly:
  - no coverage at all (baseline)
  - coverage with C tracer, line-only
  - coverage with C tracer, branch coverage
  - coverage with pure-python tracer, line-only

Reports median wall time over several repeats and the overhead ratio
relative to baseline.
"""
import gc
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import perf_workload as workload

import coverage


def timeit_once():
    gc.collect()
    t0 = time.perf_counter()
    workload.run()
    return time.perf_counter() - t0


def bench_baseline(repeats):
    return [timeit_once() for _ in range(repeats)]


def bench_coverage(repeats, **cov_kwargs):
    times = []
    for _ in range(repeats):
        cov = coverage.Coverage(data_file=None, **cov_kwargs)
        cov.start()
        t0 = time.perf_counter()
        workload.run()
        elapsed = time.perf_counter() - t0
        cov.stop()
        times.append(elapsed)
    return times


def summarize(name, times, baseline_median=None):
    med = statistics.median(times)
    ratio = f"  ratio={med / baseline_median:.2f}x" if baseline_median else ""
    print(f"{name:32s} median={med*1000:8.2f}ms  min={min(times)*1000:8.2f}ms  all={[f'{t*1000:.1f}' for t in times]}{ratio}")
    return med


if __name__ == "__main__":
    REPEATS = 7

    base_times = bench_baseline(REPEATS)
    base_med = summarize("baseline (no coverage)", base_times)

    ctrace_line = bench_coverage(REPEATS, config_file=False)
    summarize("ctrace, line-only", ctrace_line, base_med)

    ctrace_branch = bench_coverage(REPEATS, config_file=False, branch=True)
    summarize("ctrace, branch", ctrace_branch, base_med)

    pytrace_line = bench_coverage(REPEATS, config_file=False, timid=True)
    summarize("pytrace, line-only", pytrace_line, base_med)

    pytrace_branch = bench_coverage(REPEATS, config_file=False, timid=True, branch=True)
    summarize("pytrace, branch", pytrace_branch, base_med)
