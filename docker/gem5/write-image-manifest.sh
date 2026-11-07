#!/bin/sh
# Record the inputs of this gem5 image to /opt/manifest/image.json.
# Called once during docker build; expects the build args in the environment.
set -eu
cd /opt/gem5
if [ "$(dpkg --print-architecture)" = "amd64" ]; then
  apt_source="snapshot.ubuntu.com ${APT_SNAPSHOT}"
else
  apt_source="live ports.ubuntu.com mirror at build time; snapshot unavailable for arm64"
fi
mkdir -p /opt/manifest
dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' | sort \
  > /opt/manifest/apt-packages.tsv
jq -n \
  --arg ubuntu_image "${UBUNTU_IMAGE}" \
  --arg apt_source "$apt_source" \
  --arg gem5_repo "${GEM5_REPO}" \
  --arg gem5_commit "$(git rev-parse HEAD)" \
  --arg gem5_isa "${GEM5_ISA}" \
  --arg gem5_variant "${GEM5_VARIANT}" \
  --arg gem5_binary "/opt/gem5/build/${GEM5_ISA}/gem5.${GEM5_VARIANT}" \
  --arg host_arch "$(dpkg --print-architecture)" \
  --arg host_cc "$(gcc --version | head -n 1)" \
  --arg host_cxx "$(g++ --version | head -n 1)" \
  --arg scons "$(scons --version | grep -m1 'SCons:' || true)" \
  --arg host_python "$(python3 --version)" \
  --arg built_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg guest_cc "$(x86_64-linux-gnu-gcc --version | head -n 1)" \
  '{
     ubuntu_image: $ubuntu_image,
     apt_source: $apt_source,
     apt_packages: "/opt/manifest/apt-packages.tsv",
     built_at: $built_at,
     gem5: {repo: $gem5_repo, commit: $gem5_commit, isa: $gem5_isa,
            variant: $gem5_variant, binary: $gem5_binary,
            host_arch: $host_arch},
     toolchain: {host_cc: $host_cc, host_cxx: $host_cxx, scons: $scons,
                 host_python: $host_python, guest_cc: $guest_cc},
     m5_util: {binary: "/opt/gem5/util/m5/build/x86/out/m5",
               library: "/opt/gem5/util/m5/build/x86/out/libm5.a",
               include: "/opt/gem5/include"}
   }' > /opt/manifest/image.json
cat /opt/manifest/image.json
