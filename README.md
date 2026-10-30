# CPython execution engines on simulated hardware

CS 263 research project: measure how CPython's specializing interpreter, tail-call interpreter, and experimental JIT respond to changes in CPU design. Build the engines from one pinned CPython source revision with a controlled compiler toolchain, run the same Python workloads in gem5, and change one simulated hardware parameter at a time.

The primary outcome is an explanation of *why* performance differs: branch behavior, cache behavior, instruction count, and simulated execution time. Results are not available yet.

## Start here

- [Project plan](docs/project-plan.md): milestones and deliverables.
- [Experiment design](docs/experiment-design.md): comparisons, controls, measurements, and feasibility gates.
- [Decision log](docs/decisions.md): choices that still need evidence or a team decision.
- [Agent instructions](AGENTS.md): rules for reproducible work in this repository.
- [Repository skills](.agents/skills/): focused workflows for CPython builds, gem5 runs, result analysis, debugging, and verification.

## Current status

Planning only. No CPython or gem5 version, compiler, workloads, or CPU model has been selected. The first implementation milestone is one CPython build running one small workload under gem5 with verified output and useful statistics.

## References

- [CPython interpreter types](https://github.com/python/cpython/blob/main/InternalDocs/interpreter.md)
- [CPython build options](https://docs.python.org/3.14/using/configure.html)
- [CPython JIT build notes](https://github.com/python/cpython/blob/main/Tools/jit/README.md)
- [gem5 standard library overview](https://www.gem5.org/documentation/gem5-stdlib/overview)
- [pyperformance benchmark suite](https://github.com/python/pyperformance)
