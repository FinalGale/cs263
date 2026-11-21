#!/usr/bin/env python3
"""Generate the figures, tables and number macros used by report/report.tex.

    .venv/bin/python analysis/report_assets.py [--runs analysis/report_runs.json] [--out build/report/generated]

Reads only saved run data: results/raw/<run>/manifest.json, m5out/stats.txt,
hardware.resolved.json, gem5.stderr and program.stderr, plus the committed
configs. Every run named in the runs file must exist and pass its set's
required checks, or nothing is written. Every number the report prints comes
from a macro written here; report.tex types none.

Outputs (in --out):
  numbers.tex          \\newcommand macros for every number in the prose
  tab-setup.tex        pinned inputs
  tab-feasibility.tex  per-engine checks and mode evidence
  tab-counters.tex     IPC and per-1k-instruction miss rates
  tab-sweep.tex        C smoke predictor sweep
  tab-runs.tex         provenance: every run used
  fig-relative.pdf     instructions vs cycles relative to the baseline engine
  fig-startup.pdf      startup vs workload instructions
"""

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_runs import load as load_run  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "results" / "raw"

# Plot styling: one quiet grey for context, one blue accent for the finding.
GREY = "#b9b8b0"
BLUE = "#2b6fd6"
TEXT = "#222222"
MUTED = "#666666"
GRID = "#e4e4e4"
ENGINE_KEYS = {
    "cpython-default": "Default",
    "cpython-tailcall": "TailCall",
    "cpython-jit-off": "JitOff",
    "cpython-jit-on": "JitOn",
}


class ReportError(SystemExit):
    pass


def tex_escape(s):
    repl = {"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#",
            "$": r"\$", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}"}
    return "".join(repl.get(c, c) for c in str(s))


def tt(s):
    return r"\texttt{" + tex_escape(s) + "}"


def thousands(n):
    return f"{int(round(n)):,}".replace(",", "{,}")


def load_set(spec, name):
    rows = []
    for entry in spec["runs"]:
        run_dir = RAW / entry["run"]
        if not (run_dir / "manifest.json").exists():
            raise ReportError(f"[{name}] missing run {entry['run']} (results/raw is not committed; run it or fix {name}.runs)")
        manifest = json.loads((run_dir / "manifest.json").read_text())
        failed = [c for c in spec["required_checks"] if not manifest["checks"].get(c)]
        if failed:
            raise ReportError(f"[{name}] {entry['run']} fails required checks {failed}")
        if "engine" in entry and manifest["engine"] != entry["engine"]:
            raise ReportError(f"[{name}] {entry['run']} is engine {manifest['engine']}, expected {entry['engine']}")
        row = load_run(run_dir)
        row.update(entry)
        row["manifest"] = manifest
        row["dir"] = run_dir
        row["hw"] = json.loads((run_dir / "hardware.resolved.json").read_text())
        stderr = (run_dir / "gem5.stderr").read_text() if (run_dir / "gem5.stderr").exists() else ""
        row["mprotect_warnings"] = stderr.count("ignoring syscall mprotect")
        rows.append(row)
    return rows


def write(out, name, text):
    (out / name).write_text(text)


def table(colspec, header, body, note=None):
    lines = [r"\begin{tabular}{" + colspec + "}", r"\toprule", " & ".join(header) + r" \\", r"\midrule"]
    lines += [" & ".join(r) + r" \\" for r in body]
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    if note:
        lines.append(r"\par\smallskip{\footnotesize " + note + "}")
    return "\n".join(lines) + "\n"


def style_axes(ax):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)


def fig_relative(engines, base, path):
    others = [r for r in engines if r is not base]
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    style_axes(ax)
    ys = list(range(len(others)))[::-1]
    for y, r in zip(ys, others):
        ri, rc = r["insts"] / base["insts"], r["cycles"] / base["cycles"]
        ax.plot([ri, rc], [y, y], color=GREY, lw=2, zorder=1)
        ax.scatter([ri], [y], s=60, color=GREY, zorder=2, label="Instructions" if y == ys[0] else None)
        ax.scatter([rc], [y], s=60, color=BLUE, zorder=3, label="Cycles" if y == ys[0] else None)
        # Value above each dot, aligned away from the other dot so labels
        # never cross each other or the reference line.
        for v, other, weight, color in ((ri, rc, "normal", MUTED), (rc, ri, "bold", TEXT)):
            left = v < other
            ax.annotate(f"{v:.3f}", (v, y), xytext=(0, 8), textcoords="offset points",
                        ha="right" if left else "left", va="bottom", fontsize=8.5, color=color, fontweight=weight)
    ax.axvline(1.0, color=MUTED, ls=(0, (4, 3)), lw=0.9, zorder=0)
    ax.text(1.0, len(others) - 0.45, f"  {base['label']}", color=MUTED, fontsize=8.5, va="bottom")
    ax.set_yticks(ys, [r["label"] for r in others], color=TEXT)
    ax.set_xlim(0.78, 1.08)
    ax.set_ylim(-0.6, len(others) - 0.2)
    ax.set_xticks([0.8, 0.9, 1.0])
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(f"relative to {base['label']} (lower is better)", color=MUTED, fontsize=9)
    ax.legend(loc="lower right", frameon=False, fontsize=8.5, ncol=2, bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    fig.savefig(path, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def fig_startup(engines, startup, path):
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    style_axes(ax)
    ax.spines["bottom"].set_visible(False)
    ys = list(range(len(engines)))[::-1]
    for y, r in zip(ys, engines):
        s = startup[r["engine"]]["insts"] / 1e6
        total = r["insts"] / 1e6
        work = total - s
        ax.barh(y, s, color=GREY, height=0.62, label="Startup" if y == ys[0] else None)
        ax.barh(y, work, left=s, color=BLUE, alpha=0.45, height=0.62, label="Workload" if y == ys[0] else None)
        ax.text(4, y, f"{s:.0f}M · {100 * s / total:.0f}%", va="center", fontsize=8.5, color=TEXT)
        ax.text(s + 4, y, f"{work:.0f}M", va="center", fontsize=8.5, color=TEXT, fontweight="bold")
        ax.text(total + 4, y, f"{total:.0f}M total", va="center", fontsize=8.5, color=MUTED)
    ax.set_yticks(ys, [r["label"] for r in engines], color=TEXT)
    ax.set_xticks([])
    ax.set_xlim(0, 320)
    ax.legend(loc="lower left", frameon=False, fontsize=8.5, ncol=2, bbox_to_anchor=(0.0, 1.0))
    fig.tight_layout()
    fig.savefig(path, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs", type=Path, default=REPO / "analysis" / "report_runs.json")
    p.add_argument("--out", type=Path, default=REPO / "build" / "report" / "generated")
    opts = p.parse_args()
    cfg = json.loads(opts.runs.read_text())

    engines = load_set(cfg["engines"], "engines")
    startup = {r["engine"]: r for r in load_set(cfg["startup"], "startup")}
    atomic = {r["engine"]: r for r in load_set(cfg["same_stream_atomic"], "same_stream_atomic")}
    no_probe = load_set(cfg["no_probe"], "no_probe")[0]
    sweep = load_set(cfg["c_predictor_sweep"], "c_predictor_sweep")
    repeat = load_set(cfg["c_repeat"], "c_repeat")
    base = next(r for r in engines if r["engine"] == cfg["engines"]["baseline_engine"])

    # Engine mode must match what the guest reported.
    expect_mode = {
        "cpython-default": (False, False), "cpython-tailcall": (True, False),
        "cpython-jit-off": (False, False), "cpython-jit-on": (False, True),
    }
    for r in engines:
        rep = r["engine_report"]
        if rep is None:
            raise ReportError(f"{r['run']}: no ENGINE_REPORT in program.stderr")
        if (rep["tail_call_interp"], rep["jit_enabled"]) != expect_mode[r["engine"]]:
            raise ReportError(f"{r['run']}: engine report {rep} does not match {r['engine']}")

    expected = (REPO / "benchmarks" / "python-smoke" / "expected_stdout.txt").read_text()
    inner = int(re.search(r"total_steps=(\d+)", expected).group(1))

    out = opts.out
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "axes.edgecolor": GRID})

    # ---- numbers.tex
    macros = {}
    for r in engines:
        k = ENGINE_KEYS[r["engine"]]
        s = startup[r["engine"]]["insts"]
        ri, rc = r["insts"] / base["insts"], r["cycles"] / base["cycles"]
        macros.update({
            f"InstsM{k}": f"{r['insts'] / 1e6:.1f}",
            f"CyclesM{k}": f"{r['cycles'] / 1e6:.1f}",
            f"RelInsts{k}": f"{ri:.3f}",
            f"RelCycles{k}": f"{rc:.3f}",
            f"CycleSavingPct{k}": f"{(1 - rc) * 100:.1f}",
            f"InstSavingPct{k}": f"{(1 - ri) * 100:.1f}",
            f"InstExtraPct{k}": f"{(ri - 1) * 100:.1f}",
            f"StartupM{k}": f"{s / 1e6:.0f}",
            f"WorkM{k}": f"{(r['insts'] - s) / 1e6:.0f}",
            f"StartupSharePct{k}": f"{s / r['insts'] * 100:.0f}",
            f"BrMPKI{k}": f"{r['br_mpki']:.2f}",
            f"IPC{k}": f"{r['ipc']:.2f}",
            f"JitActive{k}": thousands(r["engine_report"]["jit_active_inner_iterations"]),
            f"HostMin{k}": f"{r['host_wall_seconds'] / 60:.1f}",
        })
    jit_on = next(r for r in engines if r["engine"] == "cpython-jit-on")
    jit_off = next(r for r in engines if r["engine"] == "cpython-jit-off")
    shares = [startup[r["engine"]]["insts"] / r["insts"] * 100 for r in engines]
    walls = [r["host_wall_seconds"] / 60 for r in engines]
    mips = [r["insts"] / r["host_wall_seconds"] / 1e6 for r in engines]
    work_on = jit_on["insts"] - startup["cpython-jit-on"]["insts"]
    work_base = base["insts"] - startup[base["engine"]]["insts"]
    stream_diffs = {r["label"]: int(r["insts"] - atomic[r["engine"]]["insts"]) for r in engines}
    mismatched = {k: v for k, v in stream_diffs.items() if v != 0}
    if mismatched:
        stream_note = ("O3 and the atomic CPU retired identical instruction counts for "
                       f"{len(engines) - len(mismatched)} of {len(engines)} engines; "
                       + "; ".join(f"{tex_escape(k)} differs by {abs(v)} instructions" for k, v in mismatched.items())
                       + ", for reasons not yet explained")
    else:
        stream_note = "O3 and the atomic CPU retired identical instruction counts for every engine"

    sweep_base = next(r for r in sweep if r["run"] == cfg["c_predictor_sweep"]["baseline_run"])
    sweep_deltas = [abs(r["cycles"] / sweep_base["cycles"] - 1) * 100 for r in sweep]
    sweep_insts = {int(r["insts"]) for r in sweep}
    if len(sweep_insts) != 1:
        raise ReportError(f"C sweep runs executed different instruction counts: {sweep_insts}")
    ticks = {r["run"]: int(r["manifest"]["key_stats"]["simTicks"]) for r in sweep + repeat}
    repeat_identical = len({ticks[sweep_base["run"]]} | {ticks[r["run"]] for r in repeat}) == 1
    if not repeat_identical:
        raise ReportError(f"C repeat runs differ in simTicks: {ticks}; update the report's repeatability text")

    cpy = json.loads((REPO / "configs" / "cpython" / "build.json").read_text())
    build_manifest_path = REPO / "build" / "cpython" / "default" / "build-manifest.json"
    if not build_manifest_path.exists():
        raise ReportError("build/cpython/default/build-manifest.json missing: run scripts/build_cpython.sh default")
    bm = json.loads(build_manifest_path.read_text())
    image = base["manifest"]["container"]["image_manifest"]
    run_commits = sorted({(r["manifest"]["repository"]["commit"][:7], r["manifest"]["repository"]["dirty"]) for r in engines})

    macros.update({
        "InnerIterations": thousands(inner),
        "JitActivePct": f"{jit_on['engine_report']['jit_active_inner_iterations'] / inner * 100:.1f}",
        "StartupShareMin": f"{min(shares):.0f}",
        "StartupShareMax": f"{max(shares):.0f}",
        "StartupMeanM": f"{sum(startup[r['engine']]['insts'] for r in engines) / len(engines) / 1e6:.0f}",
        "NoProbeInstsM": f"{no_probe['insts'] / 1e6:.0f}",
        "ProbeInstsM": f"{base['insts'] / 1e6:.0f}",
        "ProbeOverheadM": f"{(base['insts'] - no_probe['insts']) / 1e6:.0f}",
        "JitWorkSavingPct": f"{(1 - work_on / work_base) * 100:.0f}",
        "MprotectJit": str(jit_on["mprotect_warnings"]),
        "MprotectOther": str(base["mprotect_warnings"]),
        "HostMinMin": f"{min(walls):.1f}",
        "HostMinMax": f"{max(walls):.1f}",
        "SimMIPS": f"{sum(mips) / len(mips):.2f}",
        "InstStreamNote": stream_note,
        "BrCutPctTailCall": f"{(1 - next(r for r in engines if r['engine'] == 'cpython-tailcall')['br_mpki'] / base['br_mpki']) * 100:.0f}",
        "CSweepMaxDeltaPct": f"{max(sweep_deltas):.1f}",
        "CSweepMPKIMin": f"{min(r['br_mpki'] for r in sweep):.1f}",
        "CSweepMPKIMax": f"{max(r['br_mpki'] for r in sweep):.1f}",
        "CSweepInsts": thousands(sweep_insts.pop()),
        "CBaselineTicks": thousands(ticks[sweep_base["run"]]),
        "CPythonTag": tex_escape(cpy["cpython"]["tag"]),
        "CPythonCommit": cpy["cpython"]["commit"][:8],
        "GemCommit": image["gem5"]["commit"][:8],
        "ClangVersion": tex_escape(bm["toolchain"]["cc_version"].split(" (")[0]),
        "BuildOpt": tex_escape(bm["flags"]["OPT"]),
        "RunsCommit": ", ".join(f"{c}{' (dirty)' if d else ''}" for c, d in run_commits),
        "CpuType": tex_escape(base["hw"]["cpu"]["type"]),
        "CpuClock": tex_escape(base["hw"]["cpu"]["clock"]),
        "HwSpecName": tex_escape(base["hw"]["name"]),
    })
    numbers = ["% Generated by analysis/report_assets.py; do not edit."]
    for k, v in macros.items():
        if not re.fullmatch(r"[A-Za-z]+", k):
            raise ReportError(f"bad macro name {k}")
        numbers.append(r"\newcommand{\%s}{%s}" % (k, v))
    write(out, "numbers.tex", "\n".join(numbers) + "\n")

    # ---- tables
    hw = base["hw"]
    c = hw["caches"]
    bp = hw["branch_predictor"]["conditional"]
    write(out, "tab-setup.tex", table("@{}ll@{}", ["Component", "Pinned value"], [
        ["Simulator", f"gem5 {tt(image['gem5']['commit'][:8])}, {tex_escape(image['gem5']['isa'])} \\texttt{{gem5.{tex_escape(image['gem5']['variant'])}}}, syscall emulation"],
        ["CPython", f"{tex_escape(cpy['cpython']['tag'])} ({tt(cpy['cpython']['commit'][:8])}), static {tex_escape(cpy['target'])}"],
        ["Compiler", f"{tex_escape(bm['toolchain']['cc_version'].split(' (')[0])}, all variants"],
        ["Flags", f"{tt(bm['flags']['OPT'])}, PGO {'on' if bm['flags']['pgo'] else 'off'}, LTO {'on' if bm['flags']['lto'] else 'off'}"],
        ["CPU", f"1 {tex_escape(hw['cpu']['type'])} core, {tex_escape(hw['cpu']['clock'])}, {tex_escape(bp['class'])}"],
        ["Caches", f"L1I/L1D {tex_escape(c['l1i']['size'])} {c['l1i']['assoc']}-way, L2 {tex_escape(c['l2']['size'])} {c['l2']['assoc']}-way, prefetchers off"],
        ["Memory", tex_escape(f"{hw['memory']['class']}, {hw['memory']['size']}")],
    ], note=f"Hardware spec {tt(hw['name'])} is a proposal (decision D6)."))

    feas = []
    for r in engines:
        rep = r["engine_report"]
        binary = r["manifest"]["workload"]["binary"].split("/")[2]
        env = ", ".join(e for e in r["manifest"]["workload"]["environment"] if e.startswith("PYTHON_JIT"))
        active = rep["jit_active_inner_iterations"]
        feas.append([tex_escape(r["label"]), tt(binary), tt(env), "yes" if rep["tail_call_interp"] else "no",
                     "yes" if rep["jit_available"] else "no", "yes" if rep["jit_enabled"] else "no",
                     f"{thousands(active)} ({active / inner * 100:.1f}\\%)"])
    write(out, "tab-feasibility.tex", table("@{}llllllr@{}",
        ["Engine", "Build", "Env", "Tail-call", "JIT avail.", "JIT on", "Iters in JIT code"], feas,
        note=f"All runs accepted. Mode flags are reported by the guest itself. ``Iters in JIT code'' counts the {thousands(inner)} hot-loop iterations that saw \\texttt{{sys.\\_jit.is\\_active()}} true."))

    write(out, "tab-counters.tex", table("@{}lrrrrrr@{}",
        ["Engine", "IPC", "Br.\\ MPKI", "L1I MPKI", "L1D MPKI", "Sim.\\ time (ms)", "Host (min)"],
        [[tex_escape(r["label"]), f"{r['ipc']:.2f}", f"{r['br_mpki']:.2f}", f"{r['l1i_mpki']:.2f}",
          f"{r['l1d_mpki']:.2f}", f"{r['sim_seconds'] * 1e3:.1f}", f"{r['host_wall_seconds'] / 60:.1f}"] for r in engines],
        note="MPKI = misses (or conditional-branch mispredictions, gem5 \\texttt{condIncorrect}) per 1000 instructions. Whole process, startup included."))

    def gsize(r):
        return r["hw"]["branch_predictor"]["conditional"]["params"]["globalPredictorSize"]

    sweep_rows = []
    for r in sorted(sweep, key=gsize):
        delta = r["cycles"] / sweep_base["cycles"] - 1
        is_base = r is sweep_base
        sweep_rows.append([thousands(gsize(r)) + (" (baseline)" if is_base else ""), thousands(r["cycles"]),
                           "---" if is_base else f"{delta * 100:+.2f}\\%".replace("-", "$-$"),
                           f"{r['ipc']:.3f}", f"{r['br_mpki']:.2f}"])
    write(out, "tab-sweep.tex", table("@{}lrrrr@{}",
        ["Global table entries", "Cycles", "vs baseline", "IPC", "Br.\\ MPKI"], sweep_rows))

    prov = []
    for name in ("engines", "startup", "same_stream_atomic", "no_probe", "c_predictor_sweep", "c_repeat"):
        for entry in cfg[name]["runs"]:
            m = json.loads((RAW / entry["run"] / "manifest.json").read_text())
            prov.append([tex_escape(name.replace("_", " ")), tt(entry["run"]), tex_escape(m["status"]),
                         tt(m["repository"]["commit"][:7] + ("*" if m["repository"]["dirty"] else ""))])
    write(out, "tab-runs.tex", table("@{}lllr@{}", ["Set", "Run directory (results/raw/)", "Status", "Repo"], prov,
        note="* = working tree had uncommitted changes. Atomic-CPU runs are ``rejected'' only for lacking branch-predictor counters; the report uses their instruction counts."))

    # ---- figures
    fig_relative(engines, base, out / "fig-relative.pdf")
    fig_startup(engines, startup, out / "fig-startup.pdf")
    print(f"wrote {len(macros)} macros, 5 tables, 2 figures to {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
