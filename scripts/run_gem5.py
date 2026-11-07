#!/usr/bin/env python3
"""Run one gem5 SE simulation in the pinned container and record it.

Example (smoke test):

    scripts/run_gem5.py --label smoke-collatz \\
        --binary build/benchmarks/smoke/collatz \\
        --expected-stdout benchmarks/smoke/expected_stdout.txt -- 20000

One-factor sweeps derive from the baseline with --set, which is recorded:

    scripts/run_gem5.py ... --set caches.l1i.size=16KiB

Writes results/raw/<run_id>/ containing:
  manifest.json            inputs, versions, checks, and status
  hardware.resolved.json   the exact hardware spec passed to gem5
  gem5.stdout, gem5.stderr simulator console output
  program.stdout/.stderr   guest program output
  m5out/                   stats.txt, config.ini, config.json, sim_exit.json

Every run is kept, including failures; manifest.json says why a run is
rejected. Uses only the Python standard library on the host.
"""

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE = "cs263-gem5:v26.0.0.0-x86-opt"
CONTAINER_REPO = "/work"
# SE exit cause when the guest's last thread calls exit().
NORMAL_EXIT_CAUSE = "exiting with last active thread context"
# Counters a run must contain to enter analysis. Names verified against
# gem5 v26.0.0.0 stats.txt for the stdlib SimpleBoard with one O3 core.
REQUIRED_COUNTERS = [
    "simSeconds",
    "simTicks",
    "simInsts",
    "board.processor.cores.core.numCycles",
    "board.processor.cores.core.branchPred.lookups",
    "board.processor.cores.core.branchPred.condIncorrect",
    "board.cache_hierarchy.l1i-cache-0.overallMisses::total",
    "board.cache_hierarchy.l1d-cache-0.overallMisses::total",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def git_state():
    rev = run(["git", "rev-parse", "HEAD"], cwd=REPO).stdout.strip()
    dirty = run(["git", "status", "--porcelain"], cwd=REPO).stdout.strip()
    return {"commit": rev, "dirty": bool(dirty), "dirty_paths": dirty.splitlines()}


def apply_override(spec, assignment):
    key, sep, raw = assignment.partition("=")
    if not sep:
        raise SystemExit(f"--set needs key=value, got {assignment!r}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    node = spec
    parts = key.split(".")
    for part in parts[:-1]:
        if part not in node:
            raise SystemExit(f"--set {key}: no field {part!r} in spec")
        node = node[part]
    if parts[-1] not in node:
        raise SystemExit(f"--set {key}: no field {parts[-1]!r}; refusing to add new fields")
    node[parts[-1]] = value


def in_repo(path):
    path = Path(path).resolve()
    try:
        return path.relative_to(REPO)
    except ValueError:
        raise SystemExit(f"{path} must be inside the repository (it is mounted at {CONTAINER_REPO})")


def parse_stats(path):
    """Return {name: first value} for the first stats dump in stats.txt."""
    stats = {}
    if not path.exists():
        return stats
    for line in path.read_text().splitlines():
        if line.startswith("---------- End Simulation Statistics"):
            break
        m = re.match(r"^(\S+)\s+(\S+)", line)
        if m and not line.startswith("-"):
            stats.setdefault(m.group(1), m.group(2))
    return stats


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--label", required=True, help="short name used in the run id")
    p.add_argument("--hw", default="configs/hardware/baseline.json", type=Path)
    p.add_argument("--set", action="append", default=[], dest="overrides", metavar="KEY=VALUE")
    p.add_argument("--binary", required=True, type=Path, help="guest binary inside the repo")
    p.add_argument("--expected-stdout", type=Path, help="exact expected guest stdout")
    p.add_argument("--env", action="append", default=[], metavar="K=V", help="guest environment")
    p.add_argument("--engine", default="none", help="engine/build label for the manifest")
    p.add_argument("--image", default=DEFAULT_IMAGE)
    p.add_argument("args", nargs="*", help="guest program arguments (after --)")
    opts = p.parse_args()

    hw_base = json.loads(opts.hw.read_text())
    hw = copy.deepcopy(hw_base)
    for assignment in opts.overrides:
        apply_override(hw, assignment)

    binary_rel = in_repo(opts.binary)
    if not opts.binary.exists():
        raise SystemExit(f"binary not found: {opts.binary}")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{re.sub(r'[^A-Za-z0-9_.-]', '_', opts.label)}"
    out = REPO / "results" / "raw" / run_id
    out.mkdir(parents=True)
    out_rel = out.relative_to(REPO)
    (out / "hardware.resolved.json").write_text(json.dumps(hw, indent=2) + "\n")

    c = lambda rel: f"{CONTAINER_REPO}/{rel}"
    gem5_cmd = [
        "gem5", "-d", c(out_rel / "m5out"), c("scripts/gem5/se_run.py"),
        "--hw", c(out_rel / "hardware.resolved.json"),
        "--binary", c(binary_rel),
        "--stdout-file", c(out_rel / "program.stdout"),
        "--stderr-file", c(out_rel / "program.stderr"),
    ]
    for e in opts.env:
        gem5_cmd += ["--env", e]
    gem5_cmd += ["--", *opts.args]
    docker_cmd = [
        "docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{REPO}:{CONTAINER_REPO}", "-w", CONTAINER_REPO, opts.image, *gem5_cmd,
    ]

    image_id = run(["docker", "image", "inspect", "--format", "{{.Id}}", opts.image]).stdout.strip()
    image_manifest = run(["docker", "run", "--rm", opts.image, "cat", "/opt/manifest/image.json"])
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.monotonic()
    proc = run(docker_cmd)
    wall = time.monotonic() - t0
    (out / "gem5.stdout").write_text(proc.stdout)
    (out / "gem5.stderr").write_text(proc.stderr)

    m5out = out / "m5out"
    sim_exit_path = m5out / "sim_exit.json"
    sim_exit = json.loads(sim_exit_path.read_text()) if sim_exit_path.exists() else None
    stats = parse_stats(m5out / "stats.txt")
    stdout_path = out / "program.stdout"
    program_stdout = stdout_path.read_text() if stdout_path.exists() else None

    checks = {
        "gem5_process_exit_zero": proc.returncode == 0,
        "simulator_exit_normal": bool(sim_exit) and sim_exit["exit_cause"] == NORMAL_EXIT_CAUSE,
        "guest_exit_code_zero": bool(sim_exit) and sim_exit["exit_code"] == 0,
        "stats_present": bool(stats),
        "required_counters_present": all(k in stats for k in REQUIRED_COUNTERS),
    }
    if opts.expected_stdout:
        checks["stdout_matches_expected"] = program_stdout == opts.expected_stdout.read_text()
    missing = [k for k in REQUIRED_COUNTERS if k not in stats]
    failed = [k for k, ok in checks.items() if not ok]

    binary_build_info = opts.binary.with_name(opts.binary.name + ".build.txt")
    manifest = {
        "schema": "cs263-run-manifest/v0",
        "run_id": run_id,
        "status": "accepted" if not failed else "rejected",
        "rejection_reasons": failed + ([f"missing counters: {missing}"] if missing else []),
        "started_utc": started,
        "host_wall_seconds": round(wall, 3),
        "repository": git_state(),
        "container": {
            "image": opts.image,
            "image_id": image_id,
            "image_manifest": json.loads(image_manifest.stdout) if image_manifest.returncode == 0 else None,
        },
        "command": {"docker": shlex.join(docker_cmd), "gem5_exit_status": proc.returncode},
        "engine": opts.engine,
        "workload": {
            "binary": str(binary_rel),
            "binary_sha256": sha256(opts.binary),
            "binary_build_info": binary_build_info.read_text() if binary_build_info.exists() else None,
            "arguments": opts.args,
            "environment": opts.env,
            "expected_stdout": str(in_repo(opts.expected_stdout)) if opts.expected_stdout else None,
        },
        "hardware": {
            "base_spec": str(in_repo(opts.hw)),
            "base_spec_sha256": sha256(opts.hw),
            "overrides": opts.overrides,
            "resolved_spec": "hardware.resolved.json",
            "effective_config": "m5out/config.ini",
        },
        "measured_region": "whole guest process (startup included); no ROI markers",
        "random_seeds": "none used",
        "sim_exit": sim_exit,
        "checks": checks,
        "key_stats": {k: stats.get(k) for k in REQUIRED_COUNTERS},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"run {run_id}: {manifest['status']}")
    if failed:
        print(f"  failed checks: {failed}")
        if missing:
            print(f"  missing counters: {missing}")
        print(f"  see {out_rel}/gem5.stderr")
    for k in REQUIRED_COUNTERS:
        print(f"  {k} = {stats.get(k)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
