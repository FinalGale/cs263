# Experiment design (draft)

## Comparisons

Use one pinned CPython source revision. The default specializing interpreter is the baseline. Build a tail-call interpreter variant and a JIT-capable variant from that revision. Prefer a JIT-off/JIT-on comparison using the same JIT-capable binary when supported; that isolates the runtime JIT switch from binary build differences. Compare the tail-call build to a default-dispatch build compiled with the same supported toolchain and common optimization settings.

These are planned contrasts, subject to the feasibility gate. Do not assume all three modes are mutually exclusive or that enabling JIT means the benchmark spent time in JIT code. Record the actual configuration for each result.

## Controlled inputs

| Factor | Plan |
| --- | --- |
| CPython | One source commit and identical source patches, if any. Record configure options and C flags for each build. |
| Toolchain | Pin compiler and LLVM versions. JIT generation may use LLVM tools even if the C compiler is configured separately; record both. |
| Workload | Identical script, arguments, data files, environment, expected output, and Python hash seed across engines. |
| gem5 | Pin revision, ISA, CPU model, clock, memory, board, simulation mode, and statistics region. |
| Measurement | Define warmup and measured region. Keep process startup either included for all runs or excluded for all runs. Report which. |
| Repeats | Repeat enough to detect instability; predefine exclusion rules and retain failed-run records. |

PGO/LTO can change code layout and performance. Choose one policy before the comparison: either disable them for all variants or use the same training workload and settings for every compatible build. Record exceptions as a limitation.

## Hardware experiments

Start with a single baseline configuration. Then make separate one-factor sweeps:

1. Branch prediction: compare supported predictor models or capacities while keeping CPU pipeline and memory configuration fixed.
2. Instruction cache: vary L1 instruction-cache capacity, holding association and other cache parameters fixed where possible.
3. Data cache: vary L1 data-cache capacity with other parameters fixed.

Select actual values only after confirming the chosen gem5 CPU model exposes the needed controls. A later experiment may examine interactions, but one-factor sweeps cannot establish interactions by themselves.

## Workload selection

Use a small subset of [pyperformance](https://github.com/python/pyperformance) or similarly well-defined Python programs, pinned to a revision. Include different behavior (for example, branch-heavy Python loops, function calls, object access, and data processing) while keeping simulation cost manageable. Avoid benchmarking mostly I/O wait or package installation. Verify each workload's output independently of its timing.

## Measurements and analysis

- Primary: simulated execution time or cycles for the same measured work, plus speedup relative to the default interpreter under the *same* hardware configuration.
- Diagnostic: retired instructions, IPC, branch predictions/mispredictions, instruction/data cache accesses and misses, and relevant JIT activity if obtainable. Use only counters with confirmed meanings in the pinned gem5 model.
- Report both absolute values and normalized ratios. Include run variability where repeats differ, and avoid claims of causation from counters alone.
- Plot speedup by hardware setting for each workload and summarize across workloads only with a stated aggregation method, such as geometric mean of per-workload speedups.

## Acceptance checks

Before a run enters analysis, verify its manifest is complete, the engine mode matches the request, the benchmark result matches its expected output, the simulator exited normally, the measured region is comparable, and required counters are present. Keep rejected runs with a reason.

## Feasibility risks

- The experimental JIT may need executable-memory operations or other behavior not supported by the chosen gem5 mode. Prove this with a small hot loop before selecting a benchmark suite.
- Tail-call support depends on compiler and target. Confirm the chosen compiler produces a working build; a shared compiler version alone does not guarantee identical generated code.
- Full Python applications may use syscalls or libraries that complicate syscall emulation. Start small and move to full-system mode only if needed.
- JIT compilation time and steady-state speed answer different questions. Define both if the JIT warmup is significant.

## Documentation used for the draft

[CPython interpreter internals](https://github.com/python/cpython/blob/main/InternalDocs/interpreter.md), [CPython configure options](https://docs.python.org/3.14/using/configure.html), [JIT build notes](https://github.com/python/cpython/blob/main/Tools/jit/README.md), [gem5 standard library](https://www.gem5.org/documentation/gem5-stdlib/overview), and [gem5 simulator API](https://www.gem5.org/documentation/general_docs/stdlib_api/gem5.simulate.simulator.html).
