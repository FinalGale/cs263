"""Python smoke workload for gem5 SE feasibility (CPython engine study).

Same algorithm and output line as benchmarks/smoke/collatz.c, which serves as
the independent reference for expected_stdout.txt. stdout carries only the
result line so the expected-output check is identical for every engine.

An engine report goes to stderr as one JSON line. It includes how many
iterations of the hot inner loop observed sys._jit.is_active() == True:
evidence that the measured hot loop was executing JIT code, not just that the
JIT was enabled. The probe sits inside the hot loop because a loop becomes a
JIT trace only after ~4000 backward jumps (JUMP_BACKWARD_INITIAL_VALUE in
3.15), which the outer loop never reaches. Every engine runs the same probe,
so the workload is identical, but the probe's call overhead is part of the
measured work: this is a feasibility workload, not a benchmark.

Run with: python3.15 -S -s -B -P collatz.py LIMIT
(not -I/-E: they would ignore PYTHON_JIT and PYTHONHASHSEED from the guest env)
"""
import sys

try:
    _jit = sys._jit
    _jit_is_active = _jit.is_active
except AttributeError:  # not a 3.15 build
    _jit = None
    _jit_is_active = lambda: False


def steps(n):
    s = active = 0
    while n != 1:
        n = 3 * n + 1 if n & 1 else n // 2
        s += 1
        active += _jit_is_active()
    return s, active


def main(limit):
    total = best_steps = 0
    best = 1
    jit_active = 0
    for i in range(1, limit + 1):
        s, active = steps(i)
        total += s
        jit_active += active
        if s > best_steps:
            best_steps, best = s, i
    print(f"collatz limit={limit} total_steps={total} longest={best} steps={best_steps}")
    return jit_active


def engine_report(jit_active):
    import json
    import sysconfig
    report = {
        "version": sys.version,
        "tail_call_interp": bool(sysconfig.get_config_var("_Py_TAIL_CALL_INTERP")),
        "config_args": sysconfig.get_config_var("CONFIG_ARGS"),
        "jit_available": bool(_jit and _jit.is_available()),
        "jit_enabled": bool(_jit and _jit.is_enabled()),
        "jit_active_inner_iterations": jit_active,
        "hash_seed_env": __import__("os").environ.get("PYTHONHASHSEED"),
    }
    print("ENGINE_REPORT " + json.dumps(report, sort_keys=True), file=sys.stderr)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    engine_report(main(limit))
