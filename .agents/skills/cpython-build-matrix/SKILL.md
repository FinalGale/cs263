---
name: cpython-build-matrix
description: Build or change the CPython execution-engine variants for this CS 263 experiment. Use when selecting a CPython revision, compiler, build flags, or verifying default, tail-call, and JIT modes.
---

# CPython build matrix

Read `docs/experiment-design.md` and the relevant entries in `docs/decisions.md`. Use the pinned versions and settings already chosen. If they are still open, investigate compatibility and record the decision before treating builds as comparable.

Keep a machine-readable build manifest with the CPython commit, source patches, target ISA, C compiler and version, LLVM tools and version, configure options, environment, optimization flags, and build command. Put generated source trees and binaries outside tracked files.

Build the default-dispatch and tail-call variants with the same supported C toolchain and common flags. If a flag or dependency must differ, record it and its likely effect. For a JIT contrast, prefer JIT off/on in one JIT-capable build when supported; also record how it was enabled at runtime.

Verify each executable's identity and a deterministic smoke workload. Confirm the requested mode rather than inferring it from a successful build. For the JIT, verify both availability/enabled state and evidence that the measured hot code reached JIT execution. If that evidence is unavailable, report the limit and do not label the result a JIT execution comparison.

Use the pinned revision's CPython build documentation and `Tools/jit/README.md` for exact commands; do not copy commands from another release without checking them.
