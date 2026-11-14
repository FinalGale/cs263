#!/usr/bin/env bash
# Cross-build one CPython variant for x86-64 Linux. Runs INSIDE the
# cs263-cpython-build image with the repository mounted at /work; use
# scripts/build_cpython.sh from the host.
#
#   scripts/cpython/build_variant.sh <variant>     (variant from configs/cpython/build.json)
#
# Produces (not committed):
#   build/cpython/build-python/          native aarch64 CPython of the same commit,
#                                        used by the cross build and the JIT generator
#   build/cpython/<variant>/obj/         build tree, configure.log, make.log, install.log
#   build/cpython/<variant>/install/     prefix; bin/python3.15 is the static guest binary
#   build/cpython/<variant>/build-manifest.json
set -euo pipefail
variant="${1:?usage: build_variant.sh <variant>}"
cd /work
cfg=/work/configs/cpython/build.json
jq -e --arg v "$variant" '.variants[$v]' "$cfg" > /dev/null \
  || { echo "unknown variant: $variant" >&2; exit 2; }
src="/work/$(jq -r .cpython.source_dir "$cfg")"
want_commit="$(jq -r .cpython.commit "$cfg")"
jobs="${JOBS:-8}"
root=/work/build/cpython
bp="${root}/build-python"
target="$(jq -r .target "$cfg")"

git config --global --add safe.directory "$src" 2>/dev/null || true
got_commit="$(git -C "$src" rev-parse HEAD)"
[ "$got_commit" = "$want_commit" ] || { echo "source at $got_commit, want $want_commit" >&2; exit 1; }
[ -z "$(git -C "$src" status --porcelain)" ] || { echo "source tree not clean" >&2; exit 1; }

# The executable is python.exe when the build tree is on a case-insensitive
# filesystem (macOS bind mount), where "python" would collide with "Python/".
bp_exe() { if [ -f "${bp}/python.exe" ]; then echo "${bp}/python.exe"; else echo "${bp}/python"; fi; }

# 1. Native build Python (same commit). Only its correctness matters, not its flags.
if [ ! -f "$(bp_exe)" ]; then
  echo "== building native build-python in ${bp}"
  rm -rf "$bp"; mkdir -p "$bp"
  ( cd "$bp" && CC=clang "$src/configure" --without-ensurepip --disable-test-modules \
      > configure.log 2>&1 && make -j"$jobs" > make.log 2>&1 ) \
    || { echo "build-python failed; see ${bp}/{configure,make}.log" >&2; exit 1; }
fi
build_py="$(bp_exe)"
"$build_py" -c 'import sys; print("build-python", sys.version.split()[0])'

# 2. Cross build.
out="${root}/${variant}"
prefix="${out}/install"
rm -rf "$out"; mkdir -p "${out}/obj"
jq -r '.config_site | to_entries[] | "\(.key)=\(.value)"' "$cfg" > "${out}/config.site"
mapfile -t common_args < <(jq -r '.common_configure[]' "$cfg")
mapfile -t variant_args < <(jq -r --arg v "$variant" '.variants[$v].configure[]' "$cfg")
while IFS='=' read -r k v; do export "$k=$v"; done \
  < <(jq -r '.common_env | to_entries[] | "\(.key)=\(.value)"' "$cfg")
export CC="$(jq -r .toolchain.cc "$cfg")"
export CXX="$(jq -r .toolchain.cxx "$cfg")"
export AR="$(jq -r .toolchain.ar "$cfg")"
export RANLIB="$(jq -r .toolchain.ranlib "$cfg")"
export READELF="$(jq -r .toolchain.readelf "$cfg")"
export CONFIG_SITE="${out}/config.site"
configure_args=("${common_args[@]}" "${variant_args[@]}" "--prefix=${prefix}" "--with-build-python=${build_py}")

cd "${out}/obj"
echo "== configure ${variant}: ${configure_args[*]}"
"$src/configure" "${configure_args[@]}" > configure.log 2>&1 \
  || { echo "configure failed; see ${out}/obj/configure.log" >&2; tail -20 configure.log >&2; exit 1; }
echo "== make ${variant}"
make -j"$jobs" > make.log 2>&1 \
  || { echo "make failed; see ${out}/obj/make.log" >&2; tail -30 make.log >&2; exit 1; }
echo "== make install ${variant}"
make install > install.log 2>&1 \
  || { echo "install failed; see ${out}/obj/install.log" >&2; tail -30 install.log >&2; exit 1; }

exe="${prefix}/bin/python3.15"
[ -x "$exe" ] || { echo "missing $exe" >&2; exit 1; }
file_out="$(file -b "$exe")"
case "$file_out" in
  *x86-64*statically\ linked*|*x86-64*static-pie*) ;;
  *) echo "not a static x86-64 executable: $file_out" >&2; exit 1 ;;
esac

mk() { sed -n "s/^$1=[[:space:]]*//p" Makefile | head -n 1; }
# Engine selection appears either in pyconfig.h (tail-call) or as -D flags in
# CONFIGURE_CFLAGS_NODIST (JIT: -D_Py_TIER2=3 -D_Py_JIT); record both.
defines="$(grep -E '^#define (_Py_JIT|_Py_TIER2|_Py_TAIL_CALL_INTERP|Py_GIL_DISABLED|Py_DEBUG)\b' pyconfig.h || true)"
flag_defines="$(mk CONFIGURE_CFLAGS_NODIST | tr ' ' '\n' | grep -E '^-D' || true)"
defines="$(printf '%s\n%s\n' "$defines" "$flag_defines" | sed '/^$/d')"
missing="$(sed -n '/necessary bits to build these optional modules were not found/,/^$/p' make.log | tail -n +2 | tr -s ' \n' ' ')"
failed="$(sed -n '/Following modules built successfully but were removed\|Failed to build these modules/,/^$/p' make.log | tr -s ' \n' ' ')"

jq -n \
  --arg variant "$variant" \
  --argjson variant_spec "$(jq --arg v "$variant" '.variants[$v]' "$cfg")" \
  --arg config_sha256 "$(sha256sum "$cfg" | cut -d' ' -f1)" \
  --arg tag "$(jq -r .cpython.tag "$cfg")" --arg commit "$got_commit" \
  --arg target "$target" \
  --argjson configure_args "$(printf '%s\n' "${configure_args[@]}" | jq -R . | jq -s .)" \
  --argjson config_site "$(jq .config_site "$cfg")" \
  --argjson common_env "$(jq .common_env "$cfg")" \
  --arg cc "$CC" --arg cxx "$CXX" --arg ar "$AR" \
  --arg cc_version "$(clang --version | head -n 1)" \
  --arg ld_version "$(x86_64-linux-gnu-ld --version | head -n 1)" \
  --arg opt "$(mk OPT)" --arg basecflags "$(mk BASECFLAGS)" \
  --arg configure_cflags "$(mk CONFIGURE_CFLAGS)" \
  --arg cflags_nodist "$(mk CONFIGURE_CFLAGS_NODIST)" \
  --arg ldflags "$(mk CONFIGURE_LDFLAGS)" \
  --arg pyconfig_defines "$defines" \
  --arg missing_modules "$missing" --arg failed_modules "$failed" \
  --arg exe "${exe#/work/}" --arg exe_sha256 "$(sha256sum "$exe" | cut -d' ' -f1)" \
  --arg file_out "$file_out" \
  --arg image "${CS263_IMAGE:-unknown}" --arg image_id "${CS263_IMAGE_ID:-unknown}" \
  --argjson image_manifest "$(cat /opt/manifest/image.json)" \
  --arg build_python "$("$build_py" -c 'import sys;print(sys.version)')" \
  --arg built_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg jobs "$jobs" \
  '{schema: "cs263-cpython-build-manifest/v0", variant: $variant, variant_spec: $variant_spec,
    build_config: {path: "configs/cpython/build.json", sha256: $config_sha256},
    cpython: {tag: $tag, commit: $commit, patches: []},
    target: $target,
    configure: {args: $configure_args, config_site: $config_site, env: $common_env},
    toolchain: {cc: $cc, cxx: $cxx, ar: $ar, cc_version: $cc_version, ld: $ld_version},
    flags: {OPT: $opt, BASECFLAGS: $basecflags, CONFIGURE_CFLAGS: $configure_cflags,
            CONFIGURE_CFLAGS_NODIST: $cflags_nodist, CONFIGURE_LDFLAGS: $ldflags,
            pgo: false, lto: false},
    pyconfig_defines: ($pyconfig_defines | split("\n") | map(select(. != ""))),
    modules: {missing_optional: $missing_modules, failed: $failed_modules},
    executable: {path: $exe, sha256: $exe_sha256, file: $file_out},
    build_command: ("make -j" + $jobs + " && make install"),
    build_python: $build_python,
    image: {name: $image, id: $image_id, manifest: $image_manifest},
    built_at: $built_at}' > "${out}/build-manifest.json"
echo "== ${variant}: ${exe#/work/}"
echo "   ${file_out}"
echo "   defines: $(echo "$defines" | tr '\n' ';')"
