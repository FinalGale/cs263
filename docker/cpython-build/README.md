# CPython cross-build container

Builds static x86-64 Linux CPython executables for gem5 syscall emulation (SE). The image holds the toolchain only; the CPython source is a pinned checkout under `external/cpython` (not committed), and every build flag lives in [`configs/cpython/build.json`](../../configs/cpython/build.json).

| Input | Pinned value |
| --- | --- |
| Base image | `ubuntu:24.04` at `sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852` (same as `docker/gem5`) |
| LLVM | 21.1.8 official `LLVM-21.1.8-Linux-ARM64.tar.xz`, SHA-256 `65ce0b32…01993`, in `/opt/llvm` |
| x86-64 sysroot | Ubuntu `libc6-dev-amd64-cross` (glibc 2.39) and `binutils-x86-64-linux-gnu` (GNU ld 2.42) |
| CPython | `v3.15.2`, commit `5e58eaad7c58df58dfa8ea549c87996e01dd1077` |

LLVM 21 is the version the pinned CPython's `Tools/jit/README.md` supports, and Ubuntu 24.04 ships only up to LLVM 20. The same clang compiles all of CPython for every variant, so default, tail-call, and JIT builds share one C toolchain.

## Build

```sh
docker build -t cs263-cpython-build:llvm21.1.8 docker/cpython-build
scripts/build_cpython.sh default tailcall jit        # JOBS=8 by default
```

`scripts/build_cpython.sh` verifies the source checkout (`scripts/cpython/fetch_source.sh`), then runs `scripts/cpython/build_variant.sh` in the container for each variant. That script:

1. builds a native aarch64 CPython of the same commit in `build/cpython/build-python/` (needed by any cross build, and it runs the JIT stencil generator);
2. configures with `--host=x86_64-linux-gnu`, `--disable-shared`, `LDFLAGS=-static`, and `MODULE_BUILDTYPE=static`, so stdlib extension modules are linked into the executable (a static binary cannot `dlopen` them);
3. installs to `build/cpython/<variant>/install/` and writes `build/cpython/<variant>/build-manifest.json` (commit, configure arguments, `config.site`, toolchain versions, the resolved `OPT`/`CFLAGS`/`LDFLAGS`, engine defines, missing modules, executable SHA-256, image ID).

The install prefix is the path inside the containers (`/work/build/cpython/<variant>/install`), because gem5 SE runs the guest's file system calls against the gem5 container, where the repository is also mounted at `/work`.

## Engine variants

| Variant | Configure option | Engine evidence |
| --- | --- | --- |
| `default` | none | computed-goto dispatch (clang default) |
| `tailcall` | `--with-tail-call-interp` | `#define _Py_TAIL_CALL_INTERP 1` in `pyconfig.h`; `sysconfig.get_config_var("_Py_TAIL_CALL_INTERP")` |
| `jit` | `--enable-experimental-jit=yes-off` | `-D_Py_TIER2=3 -D_Py_JIT`; JIT off unless `PYTHON_JIT=1`; `sys._jit.is_available()`, `is_enabled()`, `is_active()` |

## Known limits

- **Missing optional modules.** No x86-64 builds of zlib, OpenSSL, libffi, mpdecimal, bzip2, xz, zstd, ncurses, readline, gdbm, uuid, or Tk are in the sysroot, so `zlib`, `_ssl`, `_hashlib`, `_ctypes`, `_decimal`, `_bz2`, `_lzma`, `_zstd`, `_curses`, `readline`, `_dbm`, `_gdbm`, `_uuid`, and `_tkinter` are not built. Benchmarks that import them will fail until those libraries are cross-built.
- **Case-insensitive bind mounts.** On macOS the build tree is case-insensitive, so CPython names the build-tree executable `python.exe` (the installed one is `bin/python3.15`).
- **arm64 only.** Only the arm64 LLVM tarball is pinned; an amd64 host would need its own pinned tarball and would produce a different image.
- `sys.version` embeds the build time, so rebuilding identical inputs changes the executable's SHA-256. Compare manifests, not hashes, to check that two builds used the same inputs.
