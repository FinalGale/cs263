---
name: verification-before-completion
description: Check evidence before reporting a completed CPython build, gem5 run, benchmark result, analysis, or code change in this CS 263 project.
---

# Verification before completion

Match each completion claim to a fresh check that can establish it. Run the relevant check and inspect its exit status and output before reporting success. State the command or artifact, result, and any limit on what was verified.

Choose checks for the actual change:

- **Build or script:** run the build or a representative invocation, plus focused tests when they exercise meaningful behavior.
- **Engine mode:** verify the executable, requested mode, and benchmark output. For a JIT result, confirm that the measured region reached JIT code, not merely that JIT support was compiled in.
- **gem5 result:** verify normal simulator exit, expected benchmark output, complete manifest, comparable measured region, and required raw counters.
- **Analysis:** regenerate the affected table or figure from raw data and inspect exclusions, normalization, and workload pairing.
- **Documentation only:** check changed links, paths, and consistency with the current decision log; do not require a full simulation.

If a check cannot run, report what remains unverified and why. Do not infer a pass from a prior run, another agent's summary, or the presence of output files alone.

Adapted for this repository from [Superpowers verification-before-completion](https://github.com/obra/superpowers/tree/main/skills/verification-before-completion); see [license notice](../SUPERPOWERS-LICENSE.md).
