---
name: gem5-experiment
description: Configure or run gem5 simulations for the CS 263 CPython engine study. Use when adding a simulator configuration, a hardware sweep, or a benchmark run.
---

# gem5 experiment

Read `docs/experiment-design.md` and the selected baseline in `docs/decisions.md`. Start with a small correctness run before expanding a matrix. Confirm that the chosen gem5 mode supports the workload, including any executable-memory behavior required by the JIT.

Represent the baseline CPU, predictor, caches, memory, clock, ISA, and simulation mode explicitly. For a one-factor sweep, derive each configuration from that baseline and change only the named parameter. Pin the gem5 commit and record the complete effective configuration for each run.

Define the measured region and whether startup and JIT warmup are included. Run the same benchmark input and expected-output check for every engine and hardware configuration. Save the simulator command, exit status, stdout/stderr, raw stats, and a machine-readable manifest. Keep failed and unsupported runs with a reason.

Before accepting a run, check output correctness, engine mode, normal simulator exit, comparable measured work, and presence of the required counters. If a gem5 counter is unavailable or has ambiguous meaning in the selected CPU model, document that and omit the affected analysis rather than substituting a different counter silently.
