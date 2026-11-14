#!/bin/sh
# Record the inputs of the CPython build image to /opt/manifest/image.json.
# Called once during docker build; expects UBUNTU_IMAGE, LLVM_VERSION and
# LLVM_ARM64_SHA256 in the environment.
set -eu
mkdir -p /opt/manifest
dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' | sort \
  > /opt/manifest/apt-packages.tsv
jq -n \
  --arg ubuntu_image "${UBUNTU_IMAGE}" \
  --arg apt_source "live ports.ubuntu.com mirror at build time; snapshot unavailable for arm64" \
  --arg host_arch "$(dpkg --print-architecture)" \
  --arg llvm_version "${LLVM_VERSION}" \
  --arg llvm_sha256 "${LLVM_ARM64_SHA256}" \
  --arg clang "$(clang --version | head -n 1)" \
  --arg gnu_cross_ld "$(x86_64-linux-gnu-ld --version | head -n 1)" \
  --arg glibc_cross "$(dpkg-query -W -f='${Version}' libc6-dev-amd64-cross)" \
  --arg gcc_cross "$(x86_64-linux-gnu-gcc --version | head -n 1)" \
  --arg host_cc "$(gcc --version | head -n 1)" \
  --arg built_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{ubuntu_image: $ubuntu_image, apt_source: $apt_source,
    apt_packages: "/opt/manifest/apt-packages.tsv", built_at: $built_at,
    host_arch: $host_arch,
    llvm: {version: $llvm_version, prefix: "/opt/llvm", tarball_sha256: $llvm_sha256, clang: $clang},
    cross: {target: "x86_64-linux-gnu", ld: $gnu_cross_ld,
            libc6_dev_amd64_cross: $glibc_cross, gcc: $gcc_cross},
    host_cc: $host_cc}' > /opt/manifest/image.json
cat /opt/manifest/image.json
