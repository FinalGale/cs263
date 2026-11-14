#!/usr/bin/env python3
"""Summarize gem5 runs from results/raw/<run_id>/ into a table.

    analysis/summarize_runs.py RUN_DIR [RUN_DIR ...] [--baseline ENGINE] [--json OUT]

Inputs are only what run_gem5.py saved: manifest.json, m5out/stats.txt, and the
guest's program.stderr (for the ENGINE_REPORT line of the Python smoke
workload). Rejected runs are listed with their reasons and excluded from
ratios; missing counters are shown as "n/a", never as zero.

Derived metrics (computed here, from raw counters):
  IPC          simInsts / core.numCycles
  br MPKI      branchPred.condIncorrect per 1000 simInsts (conditional
               mispredictions detected at execute in the O3 model)
  L1I/L1D MPKI overallMisses::total per 1000 simInsts
  rel cycles   core.numCycles / numCycles of the --baseline engine's run
"""

import argparse
import json
import re
import sys
from pathlib import Path

C = "board.processor.cores.core."
COUNTERS = {
    "insts": "simInsts",
    "cycles": C + "numCycles",
    "sim_seconds": "simSeconds",
    "br_lookups": C + "branchPred.lookups_0::total",
    "br_cond_incorrect": C + "branchPred.condIncorrect",
    "l1i_misses": "board.cache_hierarchy.l1i-cache-0.overallMisses::total",
    "l1d_misses": "board.cache_hierarchy.l1d-cache-0.overallMisses::total",
}


def parse_stats(path):
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


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(run_dir):
    run_dir = Path(run_dir)
    m = json.loads((run_dir / "manifest.json").read_text())
    stats = parse_stats(run_dir / "m5out" / "stats.txt")
    row = {
        "run_id": m["run_id"],
        "engine": m["engine"],
        "env": m["workload"]["environment"],
        "status": m["status"],
        "rejection_reasons": m["rejection_reasons"],
        "cpu": json.loads((run_dir / "hardware.resolved.json").read_text())["cpu"]["type"],
        "host_wall_seconds": m["host_wall_seconds"],
    }
    for k, name in COUNTERS.items():
        row[k] = num(stats.get(name))
    report = None
    stderr = run_dir / "program.stderr"
    if stderr.exists():
        for line in stderr.read_text().splitlines():
            if line.startswith("ENGINE_REPORT "):
                report = json.loads(line[len("ENGINE_REPORT "):])
    row["engine_report"] = report
    ins = row["insts"]

    def per_k(x):
        return None if x is None or not ins else 1000 * x / ins

    row["ipc"] = ins / row["cycles"] if ins and row["cycles"] else None
    row["br_mpki"] = per_k(row["br_cond_incorrect"])
    row["l1i_mpki"] = per_k(row["l1i_misses"])
    row["l1d_mpki"] = per_k(row["l1d_misses"])
    return row


def fmt(v, spec):
    width = int(spec.split(".")[0])
    return "n/a".rjust(width) if v is None else format(v, spec)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs", nargs="+")
    p.add_argument("--baseline", default="cpython-default")
    p.add_argument("--json", type=Path)
    opts = p.parse_args()
    rows = [load(r) for r in opts.runs]
    base = next((r for r in rows if r["engine"] == opts.baseline and r["status"] == "accepted"), None)
    for r in rows:
        ok = r["status"] == "accepted" and base and r["cycles"] and base["cycles"]
        r["rel_cycles"] = r["cycles"] / base["cycles"] if ok else None

    hdr = f"{'engine':<18}{'cpu':<7}{'status':<9}{'Minsts':>9}{'Mcycles':>9}{'rel cyc':>8}{'IPC':>6}{'brMPKI':>7}{'L1I MPKI':>9}{'L1D MPKI':>9}{'JIT active':>11}{'wall s':>8}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        rep = r["engine_report"] or {}
        jit = rep.get("jit_active_inner_iterations")
        print(
            f"{r['engine']:<18}{r['cpu']:<7}{r['status']:<9}"
            f"{fmt(r['insts'] and r['insts'] / 1e6, '9.1f')}"
            f"{fmt(r['cycles'] and r['cycles'] / 1e6, '9.1f')}"
            f"{fmt(r['rel_cycles'], '8.3f')}{fmt(r['ipc'], '6.2f')}{fmt(r['br_mpki'], '7.2f')}"
            f"{fmt(r['l1i_mpki'], '9.2f')}{fmt(r['l1d_mpki'], '9.2f')}"
            f"{'n/a' if jit is None else jit:>11}{r['host_wall_seconds']:>8.0f}"
        )
    for r in rows:
        if r["status"] != "accepted":
            print(f"  rejected {r['run_id']}: {r['rejection_reasons']}")
    if opts.json:
        opts.json.write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
