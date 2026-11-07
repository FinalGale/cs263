# gem5 container

A pinned image containing gem5 built for the **X86 guest ISA** (`build/X86/gem5.opt`), an x86-64 cross-compiler for guest programs, and the x86-64 `m5` utility and `libm5.a` for future region-of-interest markers.

| Input | Pinned value |
| --- | --- |
| Base image | `ubuntu:24.04` at `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852` |
| gem5 | `v26.0.0.0`, commit `fed0e07e930fecf1e73dce94dd44e69a5bf70c46` |
| gem5 build | `build/X86/gem5.opt` |
| Guest compiler | Ubuntu `gcc-x86-64-linux-gnu` (exact version in the image manifest) |
| apt packages | Snapshot `20261101T000000Z` on amd64 hosts; live mirror on arm64 hosts (see limits) |

The container's own architecture matches the Docker host. On Apple silicon it is `linux/arm64`, so gem5 runs natively while simulating an x86-64 CPU; nothing runs under Rosetta or QEMU.

## Build

```sh
JOBS=5 scripts/build_gem5_image.sh   # tag: cs263-gem5:v26.0.0.0-x86-opt
```

`JOBS` sets compile parallelism only. gem5 needs roughly 1-1.5 GB of RAM per job; with an 8 GB Docker VM, use 4-5. The build log goes to `results/tmp/docker-build-gem5.log` (not committed).

The image records its inputs in `/opt/manifest/image.json` and every installed package version in `/opt/manifest/apt-packages.tsv`. `scripts/run_gem5.py` copies `image.json` and the image ID into each run manifest.

```sh
docker run --rm cs263-gem5:v26.0.0.0-x86-opt cat /opt/manifest/image.json
```

## Smoke test

```sh
docker run --rm -v "$PWD":/work cs263-gem5:v26.0.0.0-x86-opt benchmarks/smoke/build.sh
scripts/run_gem5.py --label smoke-collatz \
    --binary build/benchmarks/smoke/collatz \
    --expected-stdout benchmarks/smoke/expected_stdout.txt -- 20000
```

The run goes to `results/raw/<run_id>/` with a `manifest.json` whose `status` is `accepted` only if gem5 exited normally, the guest exited 0, stdout matched, and the required counters exist.

## Known limits

- **arm64 package pinning.** `snapshot.ubuntu.com` does not serve `ubuntu-ports` (it returned HTTP 401 on 2026-11-06), so arm64 builds take packages from the live mirror. Rebuilding later can pick up newer Ubuntu point releases of the host compiler or libraries. The exact versions used are in `apt-packages.tsv`; compare them before treating two image builds as identical. The guest binaries and gem5 source do not depend on this, but the gem5 host binary does.
- **Images built on different host architectures are different images.** An amd64-built and an arm64-built image compile gem5 with different host compilers. Keep all comparative runs on one image ID.
- `gem5.opt` keeps assertions and debug flags (useful for checking JIT execution with `--debug-flags`); it is slower than `gem5.fast`. Switching variants requires a decision-log entry.
