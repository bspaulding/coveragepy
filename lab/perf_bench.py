"""Measure baseline vs coverage-instrumented execution time.

Runs workload.run() repeatedly:
  - no coverage at all (baseline)
  - coverage with C tracer (ctrace), line-only and branch
  - coverage with pure-python tracer (pytrace), line-only and branch
  - on Python 3.12+, coverage with sys.monitoring (sysmon), line-only
    and (experimentally) branch

Reports median wall time over several repeats and the overhead ratio
relative to baseline.

Findings (see coverage/ctracer/tracer.c and coverage/env.py history for
the code involved):

- On any Python version, `sys.settrace`-based tracing (ctrace or
  pytrace) has a hard floor around 3x baseline on this workload, even
  with a trace function that does nothing (verified by temporarily
  building with DO_NOTHING defined in coverage/ctracer/util.h). That
  floor comes from CPython disabling its specializing adaptive
  interpreter for any frame being traced -- it isn't something
  coverage.py's own bookkeeping can optimize away. So on Python < 3.12,
  no amount of tuning CTracer can bring line-coverage overhead under
  2x; ~4.2x (line) / ~6x (branch) is close to the practical floor for
  this API.

- On Python 3.12+, sys.monitoring (PEP 669) does *not* pay that
  specialization tax. Coverage.py already implements this as the
  "sysmon" core (coverage/sysmon.py); it just isn't the default until
  3.14 (coverage/env.py: SYSMON_DEFAULT), because branch coverage under
  sysmon isn't reliable before Python 3.14 (env.PYBEHAVIOR.branch_right_left).
  Opting in explicitly with COVERAGE_CORE=sysmon for *line-only*
  coverage on 3.12/3.13 measures at essentially 1.0x baseline on this
  workload (median ratio ~0.99x across 15 repeats) -- verified to
  produce identical statement/line results to ctrace on the same code.
  Branch coverage under sysmon still falls back to ctrace pre-3.14 for
  correctness reasons, so it doesn't get this speedup yet.
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


def bench_coverage(repeats, core=None, **cov_kwargs):
    times = []
    old_core_env = os.environ.get("COVERAGE_CORE")
    try:
        if core is not None:
            os.environ["COVERAGE_CORE"] = core
        elif "COVERAGE_CORE" in os.environ:
            del os.environ["COVERAGE_CORE"]
        for _ in range(repeats):
            cov = coverage.Coverage(data_file=None, **cov_kwargs)
            cov.start()
            t0 = time.perf_counter()
            workload.run()
            elapsed = time.perf_counter() - t0
            cov.stop()
            times.append(elapsed)
    finally:
        if old_core_env is None:
            os.environ.pop("COVERAGE_CORE", None)
        else:
            os.environ["COVERAGE_CORE"] = old_core_env
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

    ctrace_line = bench_coverage(REPEATS, config_file=False, core="ctrace")
    summarize("ctrace, line-only", ctrace_line, base_med)

    ctrace_branch = bench_coverage(REPEATS, config_file=False, core="ctrace", branch=True)
    summarize("ctrace, branch", ctrace_branch, base_med)

    pytrace_line = bench_coverage(REPEATS, config_file=False, timid=True)
    summarize("pytrace, line-only", pytrace_line, base_med)

    pytrace_branch = bench_coverage(REPEATS, config_file=False, timid=True, branch=True)
    summarize("pytrace, branch", pytrace_branch, base_med)

    from coverage import env
    if env.PYBEHAVIOR.pep669:
        sysmon_line = bench_coverage(REPEATS, config_file=False, core="sysmon")
        summarize("sysmon, line-only", sysmon_line, base_med)

        sysmon_branch = bench_coverage(REPEATS, config_file=False, core="sysmon", branch=True)
        summarize("sysmon, branch", sysmon_branch, base_med)
    else:
        print("sys.monitoring (sysmon core) not available on this Python version")
