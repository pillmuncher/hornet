# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

import time
import tracemalloc
from contextlib import contextmanager


@contextmanager
def tracemalloc_report(top: int = 10):
    """Context manager to measure memory allocations and print the top differences."""
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    try:
        yield
    finally:
        snapshot_after = tracemalloc.take_snapshot()
        stats = snapshot_after.compare_to(snapshot_before, "lineno")
        for stat in stats[:top]:
            print(stat)


@contextmanager
def timer(label: str = "Elapsed", print_result: bool = True):
    """Context manager to measure execution time of a code block."""
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        elapsed = end - start
        if print_result:
            print(f"{label}: {elapsed:.6f} seconds")
