# Decision log

Record a date, the selected option, evidence, alternatives considered, and effects on comparisons when resolving an item. Do not treat a proposal as a finalized decision.

| ID | Status | Decision needed | Current direction |
| --- | --- | --- | --- |
| D1 | Resolved for feasibility | CPython revision and target ISA | CPython `v3.15.2` (`5e58eaad`), static x86-64 Linux executables (see D1 entry). |
| D2 | Partly resolved | gem5 revision and simulation mode | gem5 v26.0.0.0 X86 `gem5.opt` in a pinned container (see D2 entry). SE mode works for a static C workload; CPython and JIT compatibility still unproven. |
| D3 | Resolved for feasibility | C compiler, LLVM tools, optimization flags, PGO/LTO policy | LLVM/clang 21.1.8 for every variant, CPython default `-O3`, no PGO/LTO, static link (see D3 entry). |
| D4 | Resolved for feasibility | Exact engine build/runtime matrix | `default`, `tailcall`, and one `jit` build run with `PYTHON_JIT=0` and `=1`; all four pass in gem5 SE (see D4 entry). |
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
  - CPython 3.15 (static, x86-64) runs under SE for every engine; see D4. The extra SE warnings for CPython are `newfstatat` flag bits, `madvise`, `rt_sigaction`, and one unsupported `ioctl` (ENOTTY), none of which changed output.
  - The stdlib `L1ICache`/`L1DCache`/`L2Cache` attach a `StridePrefetcher` by default and the stdlib private L1/L2 hierarchy fixes associativity; `se_run.py` sets every cache parameter from the spec instead.

### D1 — CPython revision and target (2026-11-13)

- **Decision (for feasibility work; revisit before comparative runs):** CPython `v3.15.2`, commit `5e58eaad7c58df58dfa8ea549c87996e01dd1077`, checked out by `scripts/cpython/fetch_source.sh` into `external/cpython` with no patches. Target `x86_64-linux-gnu`, cross-compiled in `docker/cpython-build` and linked statically for gem5 SE. Configuration: `configs/cpython/build.json`.
- **Evidence:** v3.15.2 was the newest stable tag on 2026-11-13 (3.16 is at alpha 2). Default, tail-call, and JIT variants all build from it, and all four engine configurations produced the expected output in gem5 SE on the O3 baseline (runs `results/raw/20261114T063642Z-pysmoke-*-o3`).
- **Alternatives:** 3.14.x (the JIT and tail-call interpreter are older and less mature there); a dynamically linked build with gem5 path redirects (gem5 documents only partial support when host and guest ISAs differ).
- **Consequences and follow-up:** stdlib modules that need third-party libraries are not built (see `docker/cpython-build/README.md`); `_decimal`, `zlib`, and `_ctypes` will matter for benchmark selection (D5).

### D3 — Toolchain, flags, and PGO/LTO (2026-11-13)

- **Decision (for feasibility work):** clang from the official LLVM 21.1.8 arm64 release (pinned by SHA-256) compiles all of CPython for every variant, with `--target=x86_64-linux-gnu`, Ubuntu's x86-64 glibc 2.39 sysroot, and GNU ld 2.42. CPython's default `OPT=-DNDEBUG -g -O3 -Wall` and its default frame-pointer flags apply to all variants. PGO and LTO are disabled for every variant. Linking uses `LDFLAGS=-static` and `MODULE_BUILDTYPE=static`.
- **Evidence:** the pinned `Tools/jit/README.md` requires LLVM 21 for the JIT; using that same clang for all variants avoids a compiler difference between engines. Each `build/cpython/<variant>/build-manifest.json` records the resolved flags, and they are identical apart from the engine options below.
- **Alternatives:** Ubuntu clang 20 for C plus LLVM 21 for JIT stencils only; GCC for the default build (cannot build the tail-call interpreter); PGO (training cannot run in a cross build without an x86-64 runner).
- **Consequences and follow-up:** a no-PGO/LTO build is slower than distributed CPython builds, so absolute numbers do not represent release binaries. Revisit if a PGO policy is needed for comparability with published results.

### D4 — Engine build and runtime matrix (2026-11-13)

- **Decision (for feasibility work):** three builds and four engine configurations.
  - `default`: no engine option; dispatch is computed gotos.
  - `tailcall`: `--with-tail-call-interp` (defines `_Py_TAIL_CALL_INTERP 1`).
  - `jit`: `--enable-experimental-jit=yes-off` (`-D_Py_TIER2=3 -D_Py_JIT`), run as `jit-off` (`PYTHON_JIT=0`) and `jit-on` (`PYTHON_JIT=1`).
  - Every run sets `PYTHON_JIT` and `PYTHONHASHSEED=0`, and the guest environment is exactly that list. Runs use `-S -s -B -P`, not `-I`/`-E`, which would make CPython ignore those variables.
- **Evidence:** the smoke workload `benchmarks/python-smoke/collatz.py` reports the engine from inside the guest. The tail-call build reports `_Py_TAIL_CALL_INTERP` true. Only `jit-on` reports `sys._jit.is_enabled()`. In `jit-on`, 124,215 of 134,100 hot-loop iterations observed `sys._jit.is_active()` true in gem5 (both atomic and O3), matching a run under Docker amd64 emulation. So JIT code does execute under SE even though gem5 ignores `mprotect`, which the JIT build called 5 times versus once for the other builds.
- **Alternatives:** a JIT-on tail-call build (not tested); `--enable-experimental-jit=yes` (JIT on by default) as a separate binary, rejected in favour of one binary toggled at runtime.
- **Consequences and follow-up:**
  - The smoke workload's `is_active()` probe runs in the hot loop. It adds about 60M instructions to every engine (197M → 257M for `default`), so its engine ratios partly measure builtin-call cost and are feasibility results, not findings.
  - Startup alone (`LIMIT=1`) is about 95M instructions for every engine. That is a large share of short workloads, so the measured region needs ROI markers or longer workloads (D5).
  - O3 simulation of the 210–266M-instruction smoke runs took 12.5–16 min of host time per run.

## Template for resolved entries

### Dn — Short title (YYYY-MM-DD)

- **Decision:**
- **Evidence:**
- **Alternatives:**
- **Consequences and follow-up:**
