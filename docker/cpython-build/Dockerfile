# syntax=docker/dockerfile:1
# CPython cross-build image for the CS 263 engine study.
#
# Produces static x86-64 Linux CPython executables for gem5 syscall emulation.
# The container's own architecture follows the Docker host (linux/arm64 on
# Apple silicon); CPython is cross-compiled for x86_64-linux-gnu with one
# pinned LLVM toolchain, which is also the toolchain the JIT stencils need.
#
# The CPython source is not baked in: scripts/cpython/fetch_source.sh checks
# out the pinned commit under external/cpython, and the build scripts mount
# the repository at /work. See docs/decisions.md (D1, D3, D4).

# Same base as docker/gem5 (ubuntu:24.04 resolved on 2026-11-06), so the x86-64
# glibc sysroot matches the one the gem5 smoke workload was built against.
ARG UBUNTU_IMAGE=ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${UBUNTU_IMAGE}
ARG UBUNTU_IMAGE

# LLVM 21 is the version CPython 3.15's Tools/jit/README.md supports; Ubuntu
# 24.04 ships at most LLVM 20. Official release tarball, pinned by SHA-256
# (from the GitHub release asset digest, 2026-11-13).
ARG LLVM_VERSION=21.1.8
ARG LLVM_ARM64_SHA256=65ce0b329514e5643407db2d02a5bd34bf33d159055dafa82825c8385bd01993

ENV DEBIAN_FRONTEND=noninteractive

# arm64 hosts cannot use snapshot.ubuntu.com (no ubuntu-ports); package
# versions are recorded in /opt/manifest/apt-packages.tsv instead.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils git file jq make pkg-config \
        build-essential \
        gcc-x86-64-linux-gnu g++-x86-64-linux-gnu libc6-dev-amd64-cross \
        binutils-x86-64-linux-gnu; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    test "$(dpkg --print-architecture)" = "arm64" || \
        { echo "only the arm64 LLVM tarball is pinned"; exit 1; }; \
    curl -fsSL -o /tmp/llvm.tar.xz \
        "https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_VERSION}/LLVM-${LLVM_VERSION}-Linux-ARM64.tar.xz"; \
    echo "${LLVM_ARM64_SHA256}  /tmp/llvm.tar.xz" | sha256sum -c -; \
    mkdir -p /opt/llvm; \
    tar -xJf /tmp/llvm.tar.xz -C /opt/llvm --strip-components=1; \
    rm /tmp/llvm.tar.xz; \
    /opt/llvm/bin/clang --version

ENV PATH=/opt/llvm/bin:${PATH}

COPY write-image-manifest.sh /opt/manifest/write-image-manifest.sh
RUN UBUNTU_IMAGE="${UBUNTU_IMAGE}" LLVM_VERSION="${LLVM_VERSION}" \
    LLVM_ARM64_SHA256="${LLVM_ARM64_SHA256}" \
    sh /opt/manifest/write-image-manifest.sh

WORKDIR /work
