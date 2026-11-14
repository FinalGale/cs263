#!/usr/bin/env bash
# Check out the pinned CPython commit (configs/cpython/build.json) into
# external/cpython (not committed). Safe to rerun: verifies an existing tree.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cfg="${repo_root}/configs/cpython/build.json"
url="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["cpython"]["repo"])' "$cfg")"
tag="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["cpython"]["tag"])' "$cfg")"
commit="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["cpython"]["commit"])' "$cfg")"
src="${repo_root}/external/cpython"
if [ ! -d "${src}/.git" ]; then
  git clone --quiet --depth 1 --branch "${tag}" "${url}" "${src}"
fi
actual="$(git -C "${src}" rev-parse HEAD)"
if [ "${actual}" != "${commit}" ]; then
  echo "external/cpython is at ${actual}, expected ${commit} (${tag})" >&2
  exit 1
fi
if [ -n "$(git -C "${src}" status --porcelain)" ]; then
  echo "external/cpython has local changes; the build expects a clean tree" >&2
  git -C "${src}" status --short >&2
  exit 1
fi
echo "CPython ${tag} at ${commit}: clean"
