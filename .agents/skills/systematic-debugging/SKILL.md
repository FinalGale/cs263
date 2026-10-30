---
name: systematic-debugging
description: Investigate a failing CPython build, gem5 run, benchmark, or analysis step in this CS 263 project before changing its implementation or configuration.
---

# Systematic debugging

When an experiment step fails or produces an unexpected result, preserve its command, manifest, output, and exit status. Reproduce the issue with the smallest representative workload or configuration that still shows it. If reproduction is intermittent, record the frequency and environment rather than treating one clean retry as a fix.

Locate the failing boundary: CPython build, engine activation, benchmark correctness, gem5 execution, statistics extraction, or analysis. Compare the failed run with the last known good run, including source revisions, flags, inputs, and simulator settings. Form a specific hypothesis supported by the evidence before changing code or configuration.

Make the smallest change that tests the hypothesis, rerun the original failure case, and check for a regression in the adjacent working case. Document the cause, the evidence, the change, and any unresolved uncertainty. Keep failed-run records; do not delete or recast them as valid measurements.

For performance surprises, first check equal measured work and correct engine mode. A counter difference is a clue to investigate, not proof of a hardware mechanism.

Adapted for this repository from [Superpowers systematic-debugging](https://github.com/obra/superpowers/tree/main/skills/systematic-debugging); see [license notice](../SUPERPOWERS-LICENSE.md).
