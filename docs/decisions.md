# Decision log

Record a date, the selected option, evidence, alternatives considered, and effects on comparisons when resolving an item. Do not treat a proposal as a finalized decision.

| ID | Status | Decision needed | Current direction |
| --- | --- | --- | --- |
| D1 | Open | CPython revision and target ISA | One pinned recent release on Linux x86-64, subject to all engines building. |
| D2 | Partly resolved | gem5 revision and simulation mode | gem5 v26.0.0.0 X86 `gem5.opt` in a pinned container (see D2 entry). SE mode works for a static C workload; CPython and JIT compatibility still unproven. |
| D3 | Open | C compiler, LLVM tools, optimization flags, PGO/LTO policy | One compatible toolchain and common settings, with differences recorded. |
| D4 | Open | Exact engine build/runtime matrix | Default dispatch, tail-call dispatch, JIT-capable binary with JIT off/on where feasible. |
| D5 | Open | Benchmark subset and measured region | Small, deterministic, CPU-bound set; distinguish startup and steady-state. |
| D6 | Open | Baseline CPU and predictor/cache sweep values | Proposal: `configs/hardware/baseline.json` (O3, 3 GHz, TournamentBP, 32 KiB 8-way L1I/L1D, 1 MiB 16-way L2, prefetchers off). Sweep values not chosen. |
| D7 | Open | Repeats, statistical summary, and raw-data storage | Define before collecting comparative results. |

## Entries

### D2 — gem5 revision, build, and container (2026-11-06)

- **Decision (for feasibility work; revisit before comparative runs):** gem5 `v26.0.0.0`, commit `fed0e07e930fecf1e73dce94dd44e69a5bf70c46`, built as `build/X86/gem5.opt` inside `docker/gem5/Dockerfile` on `ubuntu:24.04` pinned by digest. On Apple silicon the container is native `linux/arm64` and simulates an x86-64 guest. Guest binaries are cross-compiled with Ubuntu's `x86_64-linux-gnu-gcc` 13.3.0. Simulation mode starts as syscall emulation (SE) using the gem5 standard library (`scripts/gem5/se_run.py`).
- **Evidence:** v26.0.0.0 was the newest gem5 tag on 2026-11-06. Image `sha256:5bec718c5a56…` built successfully. Smoke run `results/raw/20261107T015213Z-smoke-collatz` (static C, `benchmarks/smoke/`) was accepted: gem5 exited normally, guest exit code 0, stdout matched the independently computed expected line, and all required counters were present. A repeat produced the same `simTicks` (2438711514). A run with `caches.l1i.size=16KiB` changed only that field in `config.ini`.
- **Alternatives:** an emulated `linux/amd64` container (simpler, native x86 CPython builds, but gem5 would run under Rosetta/QEMU); `gem5.fast` (faster, but loses debug flags needed to check JIT execution); gem5 v25.1.
- **Consequences and follow-up:**
  - The final link of `gem5.opt` was OOM-killed in an 8 GB Docker VM; the build now uses gem5's `--limit-ld-memory-usage` (bfd `--no-keep-memory`). This affects the host binary only, not simulated behaviour.
  - Ubuntu's snapshot service does not serve arm64 (`ubuntu-ports`), so arm64 images use the live mirror; exact package versions are in `/opt/manifest/apt-packages.tsv`. Comparative runs must share one image ID.
  - HDF5 stats output is disabled (library not installed); text `stats.txt` is used.
  - gem5 SE logged `ignoring syscall mprotect`, `rseq`, and `set_robust_list` for the static smoke binary. Ignored `mprotect` matters for the JIT (D4): test whether CPython's JIT runs correctly and whether its code really executes before relying on SE.
  - CPython must be built for x86-64 by cross-compilation. A static or carefully redirected dynamic build is needed because gem5 notes that dynamically linked SE binaries are only partially supported when host and guest ISAs differ.
  - The stdlib `L1ICache`/`L1DCache`/`L2Cache` attach a `StridePrefetcher` by default and the stdlib private L1/L2 hierarchy fixes associativity; `se_run.py` sets every cache parameter from the spec instead.

## Template for resolved entries

### Dn — Short title (YYYY-MM-DD)

- **Decision:**
- **Evidence:**
- **Alternatives:**
- **Consequences and follow-up:**
