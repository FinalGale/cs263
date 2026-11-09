#!/usr/bin/env bash
# Build the smoke workload for the x86-64 guest. Run inside the gem5 image:
#   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work cs263-gem5:v26.0.0.0-x86-opt benchmarks/smoke/build.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
out=build/benchmarks/smoke
mkdir -p "${out}"
CC=x86_64-linux-gnu-gcc
CFLAGS="-O2 -static"
${CC} ${CFLAGS} -o "${out}/collatz" benchmarks/smoke/collatz.c
{
  echo "compiler: $(${CC} --version | head -n 1)"
  echo "cflags: ${CFLAGS}"
  echo "source_sha256: $(sha256sum benchmarks/smoke/collatz.c | cut -d' ' -f1)"
  echo "binary_sha256: $(sha256sum "${out}/collatz" | cut -d' ' -f1)"
  file "${out}/collatz"
} | tee "${out}/collatz.build.txt"
