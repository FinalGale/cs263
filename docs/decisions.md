# Decision log

Record a date, the selected option, evidence, alternatives considered, and effects on comparisons when resolving an item. Do not treat a proposal as a finalized decision.

| ID | Status | Decision needed | Current direction |
| --- | --- | --- | --- |
| D1 | Open | CPython revision and target ISA | One pinned recent release on Linux x86-64, subject to all engines building. |
| D2 | Open | gem5 revision and simulation mode | Try syscall emulation first; confirm JIT and benchmark compatibility. |
| D3 | Open | C compiler, LLVM tools, optimization flags, PGO/LTO policy | One compatible toolchain and common settings, with differences recorded. |
| D4 | Open | Exact engine build/runtime matrix | Default dispatch, tail-call dispatch, JIT-capable binary with JIT off/on where feasible. |
| D5 | Open | Benchmark subset and measured region | Small, deterministic, CPU-bound set; distinguish startup and steady-state. |
| D6 | Open | Baseline CPU and predictor/cache sweep values | Pick after inspecting supported controls and simulation cost. |
| D7 | Open | Repeats, statistical summary, and raw-data storage | Define before collecting comparative results. |

## Template for resolved entries

### Dn — Short title (YYYY-MM-DD)

- **Decision:**
- **Evidence:**
- **Alternatives:**
- **Consequences and follow-up:**
