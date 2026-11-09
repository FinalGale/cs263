# CPython execution engines on simulated hardware

CS 263 research project: measure how CPython's specializing interpreter, tail-call interpreter, and experimental JIT respond to changes in CPU design. Build the engines from one pinned CPython source revision with a controlled compiler toolchain, run the same Python workloads in gem5, and change one simulated hardware parameter at a time.

The primary outcome is an explanation of _why_ performance differs: branch behavior, cache behavior, instruction count, and simulated execution time. Results are not available yet.

## Start here

- [Project plan](docs/project-plan.md): milestones and deliverables.
- [Experiment design](docs/experiment-design.md): comparisons, controls, measurements, and feasibility gates.
- [Decision log](docs/decisions.md): choices that still need evidence or a team decision.
- [Agent instructions](AGENTS.md): rules for reproducible work in this repository.
- [Repository skills](.agents/skills/): focused workflows for CPython builds, gem5 runs, result analysis, debugging, and verification.

## Current status

Phase 0 (feasibility) in progress. A pinned gem5 v26.0.0.0 container builds and runs: a static x86-64 C smoke workload completes under syscall emulation with verified output and statistics. No CPython build, engine comparison, or benchmark result exists yet. The baseline hardware in `configs/hardware/baseline.json` is a proposal.

## Quick start

```sh
JOBS=5 scripts/build_gem5_image.sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work cs263-gem5:v26.0.0.0-x86-opt benchmarks/smoke/build.sh
scripts/run_gem5.py --label smoke-collatz --binary build/benchmarks/smoke/collatz \
    --expected-stdout benchmarks/smoke/expected_stdout.txt -- 20000
```

See [docker/gem5/README.md](docker/gem5/README.md) for pinned inputs and limits. Runs land in `results/raw/<run_id>/` (not committed) with a `manifest.json`.

## References

- [CPython interpreter types](https://github.com/python/cpython/blob/main/InternalDocs/interpreter.md)
- [CPython build options](https://docs.python.org/3.14/using/configure.html)
- [CPython JIT build notes](https://github.com/python/cpython/blob/main/Tools/jit/README.md)
- [gem5 standard library overview](https://www.gem5.org/documentation/gem5-stdlib/overview)
- [pyperformance benchmark suite](https://github.com/python/pyperformance)
