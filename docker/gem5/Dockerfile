# gem5 simulator image for the CS 263 CPython engine study.
#
# Builds gem5 for the X86 guest ISA (syscall-emulation capable) plus an
# x86-64 cross toolchain for guest workloads. The container's own (host)
# architecture follows the Docker host; on Apple silicon it is linux/arm64,
# so gem5 runs natively while simulating x86-64.
#
# Every input that can change the simulator binary is a pinned build arg.
# See docs/decisions.md (D2) and docker/gem5/README.md.

# ubuntu:24.04 resolved on 2026-11-06.
ARG UBUNTU_IMAGE=ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
FROM ${UBUNTU_IMAGE}
ARG UBUNTU_IMAGE

# Ubuntu snapshot timestamp: freezes apt package versions.
ARG APT_SNAPSHOT=20261101T000000Z
# gem5 v26.0.0.0
ARG GEM5_REPO=https://github.com/gem5/gem5.git
ARG GEM5_COMMIT=fed0e07e930fecf1e73dce94dd44e69a5bf70c46
ARG GEM5_ISA=X86
ARG GEM5_VARIANT=opt
# Parallel compile jobs. gem5 needs roughly 1-1.5 GB RAM per job.
ARG JOBS=4

ENV DEBIAN_FRONTEND=noninteractive

# Package pinning: on amd64 hosts apt uses the dated Ubuntu snapshot. The
# snapshot service does not serve ubuntu-ports (arm64), so arm64 images use the
# live noble mirror and record every installed version in
# /opt/manifest/apt-packages.tsv instead. ca-certificates always comes from the
# live mirror because the snapshot service requires HTTPS.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
        sed -i -E "s#http://(archive|security).ubuntu.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/${APT_SNAPSHOT}/#" /etc/apt/sources.list.d/ubuntu.sources; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential m4 scons python3 python3-dev git pkg-config \
        zlib1g-dev libprotobuf-dev protobuf-compiler libprotoc-dev \
        libgoogle-perftools-dev libpng-dev libelf-dev libcapstone-dev \
        gcc-x86-64-linux-gnu g++-x86-64-linux-gnu libc6-dev-amd64-cross \
        file jq; \
    rm -rf /var/lib/apt/lists/*

# Fetch exactly one gem5 commit.
RUN set -eux; \
    git init /opt/gem5; \
    cd /opt/gem5; \
    git remote add origin "${GEM5_REPO}"; \
    git fetch --depth 1 origin "${GEM5_COMMIT}"; \
    git checkout --detach FETCH_HEAD; \
    test "$(git rev-parse HEAD)" = "${GEM5_COMMIT}"

WORKDIR /opt/gem5

# gem5 simulator binary. --ignore-style skips the git-hook installer.
RUN set -eux; \
    scons --ignore-style "build/${GEM5_ISA}/gem5.${GEM5_VARIANT}" -j"${JOBS}"; \
    ln -s "/opt/gem5/build/${GEM5_ISA}/gem5.${GEM5_VARIANT}" /usr/local/bin/gem5; \
    gem5 --version 2>&1 | tail -n 5 || true

# libm5 / m5 utility for the x86-64 guest, used later for region-of-interest
# markers (m5_work_begin/m5_work_end, m5_reset_stats/m5_dump_stats).
RUN set -eux; \
    cd util/m5; \
    scons --ignore-style build/x86/out/m5 build/x86/out/libm5.a \
        x86.CROSS_COMPILE=x86_64-linux-gnu- -j"${JOBS}"

# Image manifest: exact inputs, recorded inside the image for run manifests.
COPY write-image-manifest.sh /opt/manifest/write-image-manifest.sh
RUN UBUNTU_IMAGE="${UBUNTU_IMAGE}" APT_SNAPSHOT="${APT_SNAPSHOT}" \
    GEM5_REPO="${GEM5_REPO}" GEM5_ISA="${GEM5_ISA}" GEM5_VARIANT="${GEM5_VARIANT}" \
    sh /opt/manifest/write-image-manifest.sh

WORKDIR /work
