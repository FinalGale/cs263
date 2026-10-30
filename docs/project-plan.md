# Project plan

## Research question

How do branch prediction and cache configuration affect the relative performance of CPython's specializing interpreter, tail-call interpreter, and experimental JIT when compiler, source revision, workload, and other simulated hardware settings are controlled?

The initial comparison is within one CPython release. It cannot by itself establish whether gains across *releases* came from interpreter design, because other software changes also occur between releases. A cross-release study would require a separate controlled experiment.

## Milestones

| Phase | Work | Done when |
| --- | --- | --- |
| 0. Feasibility | Pin CPython, gem5, compiler/LLVM, host environment, and target ISA. Build a small CPython executable and run a deterministic script in gem5. Check JIT execution, tail-call support, required syscalls, and useful stats. | One documented end-to-end run; each engine has a pass/fail feasibility note. |
| 1. Build matrix | Automate the selected engine builds with shared flags and a recorded manifest. Verify build identity and runtime mode. | Rebuilds are repeatable and all chosen variants pass the same smoke workload. |
| 2. Benchmark selection | Choose a small, diverse subset of Python workloads with fixed inputs and expected outputs. Establish native reference runs. | Each benchmark runs correctly in every feasible engine and finishes within the simulation budget. |
| 3. Baseline simulation | Run each engine and benchmark with one fixed gem5 CPU, cache, memory, and predictor configuration. Repeat runs where measurement variability requires it. | Raw stats and complete manifests exist for every accepted run. |
| 4. Hardware sweeps | Change one predictor or cache parameter at a time, rerunning the same engine and workload matrix. | The planned matrix is complete, or exclusions have documented reasons. |
| 5. Analysis | Compute relative performance and hardware counters, check uncertainty and correctness, and explain likely mechanisms. | Reproducible tables/figures and a written discussion of findings and limits. |

## First implementation slice

1. Pick a Linux x86-64 CPython revision and a compatible gem5 revision; record exact commit hashes.
2. Select the compiler version that supports both tail-call and JIT builds. Keep normal CPython C compilation flags identical across variants where their build requirements allow it.
3. Use a tiny deterministic, mostly CPU-bound Python program to test gem5 syscall emulation first. Confirm its printed result, exit status, and stats file.
4. Build tail-call and JIT variants, then verify that the requested mode is active. For JIT, find evidence that the timed code reached compiled execution.
5. Decide whether syscall emulation is sufficient; if not, document the gap and evaluate full-system simulation before scaling up.

## Outputs to keep in Git

Versioned build/run scripts, configuration files, selected benchmark definitions, verification checks, result parsers, plotting code, a small example manifest, and final figures/report. Store bulky raw data outside Git with a documented location and checksums.

## Immediate open decisions

See [decision log](decisions.md). Set these before accepting comparative results: exact versions, simulator mode, engine matrix, benchmark subset, baseline hardware, sweep values, run count, and data storage location.
