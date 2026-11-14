#!/usr/bin/env bash
# Build CPython variants in the pinned builder image.
#   scripts/build_cpython.sh default tailcall jit
# Variants and flags: configs/cpython/build.json. Output: build/cpython/<variant>/.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["image"])' "${repo_root}/configs/cpython/build.json")"
image_id="$(docker image inspect --format '{{.Id}}' "$image")"
"${repo_root}/scripts/cpython/fetch_source.sh"
for variant in "$@"; do
  docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e JOBS="${JOBS:-8}" \
    -e CS263_IMAGE="$image" -e CS263_IMAGE_ID="$image_id" \
    -v "${repo_root}":/work -w /work "$image" scripts/cpython/build_variant.sh "$variant"
done
