---
name: analyze-results
description: Analyze or plot measured CPython and gem5 results for the CS 263 study. Use when parsing run output, comparing engines, summarizing hardware sweeps, or drafting findings.
---

# Analyze results

Read `docs/experiment-design.md` and the current decisions before choosing metrics or comparisons. Use raw stats plus run manifests as input, and keep analysis scripts and figure definitions in Git so results can be regenerated.

Reject or flag runs that failed output checks, requested the wrong engine mode, exited abnormally, lack required metadata, or measured different work. Preserve these records and state the exclusion rule. Never fill gaps with zeroes or inferred values.

Compare engines within the same benchmark and hardware setting. Report absolute simulated time or cycles alongside speedup relative to the baseline interpreter. Pair branch and cache counters with the pinned gem5 model's definitions; distinguish measured correlations from proposed mechanisms. For aggregate speedups, state the workload set and aggregation method. Show variability when repeated runs differ.

When drafting conclusions, identify what the experiment supports and what remains confounded, including build-flag differences, JIT warmup, simulator limitations, and workload selection. Do not claim a cross-release design improvement from a single-revision comparison.
