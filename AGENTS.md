# Agent working agreement

This repository is a reproducible computer architecture experiment. Before changing code or plans, read `README.md`, `docs/project-plan.md`, `docs/experiment-design.md`, and `docs/decisions.md` as relevant to the task.

## Work in small, reviewable steps

1. State the research question or implementation goal for the change.
2. Check the pinned tool and source versions once they exist. Do not silently substitute a newer CPython, gem5, LLVM, benchmark, or CPU configuration.
3. Keep build scripts, simulator configuration, benchmark definitions, and analysis separate. Record every flag and input that can affect a result.
4. For code changes, run the smallest useful verification and report the command, outcome, and limits. For documentation changes, check links, paths, and consistency with the other plans.
5. Update `docs/decisions.md` when a choice changes the experiment or its interpretation. Update the plan's status when a milestone is finished.

## Measurement rules

- Never invent timings, statistics, successful runs, or citations. Label proposed values as proposals and measured values as results.
- Save raw simulator output and a machine-readable run manifest before making plots or summaries. A manifest should identify source revisions, compiler and flags, build variant, benchmark and input, gem5 configuration, random seeds if applicable, and run status.
- Compare engines on identical workloads and simulated hardware. When studying one CPU parameter, keep the rest fixed and record the exact baseline.
- Verify benchmark output and engine mode before accepting performance data. A JIT-enabled executable does not prove JIT code ran in the measured region.
- Do not commit generated binaries, CPython or gem5 source trees, benchmark environments, or bulk simulation output. Commit scripts, small fixture inputs, configuration, and analysis code.
- Treat failed runs and unsupported configurations as findings to document, never as zero or missing values to silently discard.

## Suggested repository layout as implementation grows

`configs/` for versioned experiment specifications, `scripts/` for build and run entry points, `benchmarks/` for fixed workloads and expected outputs, `analysis/` for parsing and figures, and `docs/` for protocol and decisions. Add directories only when they contain real work.
