#!/usr/bin/env bash
# Run the Python smoke workload in gem5 for every engine configuration, in
# parallel (one gem5 process each). Each run is recorded by scripts/run_gem5.py.
#
#   scripts/run_python_smoke.sh [LABEL_SUFFIX] [HW_SPEC] [LIMIT]
#
# Engine configurations (build variant + runtime switch):
#   default        build/cpython/default,  PYTHON_JIT=0
#   tailcall       build/cpython/tailcall, PYTHON_JIT=0
#   jit-off        build/cpython/jit,      PYTHON_JIT=0
#   jit-on         build/cpython/jit,      PYTHON_JIT=1
# PYTHON_JIT is set for every engine so the guest environments differ only in
# that one value. The guest environment is exactly the --env list.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
suffix="${1:-o3}"
hw="${2:-configs/hardware/baseline.json}"
limit="${3:-2000}"
expected=()
if [ "$limit" = 2000 ]; then
  expected=(--expected-stdout benchmarks/python-smoke/expected_stdout.txt)
fi
run() {  # engine variant jit
  scripts/run_gem5.py --label "pysmoke-$1-$suffix" --engine "cpython-$1" --hw "$hw" \
    --binary "build/cpython/$2/install/bin/python3.15" ${expected[@]+"${expected[@]}"} \
    --env PYTHONHASHSEED=0 --env "PYTHON_JIT=$3" \
    -- -S -s -B -P /work/benchmarks/python-smoke/collatz.py "$limit"
}
pids=()
run default default 0 & pids+=($!)
run tailcall tailcall 0 & pids+=($!)
run jit-off jit 0 & pids+=($!)
run jit-on jit 1 & pids+=($!)
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done  # bash 3.2 (macOS) has no wait -n
exit $status
