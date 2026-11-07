#!/usr/bin/env bash
# Build the pinned gem5 Docker image. Pinned inputs live in docker/gem5/Dockerfile;
# override JOBS only (it does not change the produced simulator).
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="${GEM5_IMAGE:-cs263-gem5:v26.0.0.0-x86-opt}"
jobs="${JOBS:-4}"
log_dir="${repo_root}/results/tmp"
mkdir -p "${log_dir}"
log="${log_dir}/docker-build-gem5.log"
echo "Building ${image} with JOBS=${jobs}; log: ${log}"
docker build --progress=plain --build-arg JOBS="${jobs}" \
  -t "${image}" "${repo_root}/docker/gem5" 2>&1 | tee "${log}"
docker image inspect --format '{{.Id}}' "${image}"
