# Phase 04 Evidence — Direct MoonRay Bridge Prototype

Observed 2026-09-10 inside the `MoonRay-Rocky9` WSL2 distro, against the
installed Phase 03 runtime (`/root/moonray-blender/install/openmoonray`).

## Files
- [`build-configure-summary.txt`](build-configure-summary.txt) — CMake configure/build
  excerpts for `moonray_bridge` (`scripts/linux/phase04_build_bridge.sh`), binary
  checksum, `ldd` result.
- [`smoke-test-run.txt`](smoke-test-run.txt) — full stdout of the automated smoke
  test (`bridge/tests/run_phase04_tests.py`), 14/14 checks passed, mapped to each
  acceptance-criteria bullet in `docs/phases/04-direct-bridge-prototype.md`.

Raw build logs (`configure.log`, `build.log`) and the WSL-native bridge log
(`moonray_bridge.log`) stay under `/root/moonray-blender/logs/phase04-build/`
(WSL-native, not committed here) — same convention as Phase 03: excerpts here
are sufficient to verify acceptance, full logs add no further verification
value.

## A real crash was found and fixed during evidence-gathering — full account

The first working build of `moonray_bridge` passed the version-handshake and
`CREATE_SCENE` checks, then reliably **crashed** during `START_RENDER`
(`startFrame()`), every time, on the exact same known-good scene
(`testdata/rectangle.rdla`) that Phase 03 already proved renders correctly via
the `moonray` CLI. The bridge's own log showed, repeated across many MCRT
threads:

```
Error: Block size too small to satisfy allocation in arena allocator, 861287194624 wanted (64 byte aligned), 33554432 block size.
Error: Block size too small to satisfy allocation in arena allocator, 215321798656 wanted (64 byte aligned), 33554432 block size.
Error: Block size too small to satisfy allocation in arena allocator, 2368539785216 wanted (64 byte aligned), 33554432 block size.
```

— i.e. individual allocation requests in the hundreds-of-GB to multi-TB range,
on a machine with 15 GiB of WSL RAM, for a 512×512 test render. `dmesg`
recorded a kernel-level fault register dump and
`systemd-coredump: Failed to connect to coredump service` at the same time.
Between two evidence-gathering attempts, `dmesg` also showed a fresh WSL boot
sequence (`systemd-rc-local-generator`, `journald` "flush runtime journal") —
consistent with, though not conclusively isolated to, this crash having
destabilized the WSL2 VM itself rather than only the one process. No claim is
made beyond this temporal correlation.

### Root cause
`moonray::rendering::rndr::RenderContext` stores its `RenderOptions` argument
**by reference**, not by value:

```cpp
// moonray/rendering/rndr/RenderContext.h
explicit RenderContext(RenderOptions& options, std::stringstream* initMessages = nullptr);
...
private:
    RenderOptions& mOptions;
```

`RenderSession::createScene()` originally constructed a **local**
`moonray::rndr::RenderOptions options;` on the stack and passed it to the
`RenderContext` constructor, then returned — destroying `options` while
`mRenderContext` (a class member outliving the function call) still held a
reference to it. Every subsequent access to `mOptions` inside
`RenderContext::startFrame()` (thread count, execution mode, etc.) was a
textbook use-after-free, reading whatever the stack happened to contain by
then — explaining both the astronomically large, non-random "wanted" values
(deterministic garbage from stack reuse, not a legitimate size) and the
crash's perfect reproducibility (same scene, same stack layout each run).

A first fix (moving `RenderOptions` into a `RenderSession` member instead of a
local) was not sufficient on its own and still crashed identically. Comparing
against the reference implementation
(`moonray/cmd/raas_cmd/moonray/moonray.cc`) showed it uses **exactly one**
`RenderOptions` instance for *both* `moonray::rndr::initGlobalDriver()` *and*
every `RenderContext` it constructs — the bridge was instead using two
separate instances (one in `main()` for `initGlobalDriver()`, a second owned
by `RenderSession`). The final fix makes `main()` own a single process-wide
`RenderOptions`, passed by reference into `initGlobalDriver()` once and into
every `RenderSession`/`RenderContext` thereafter, matching the CLI exactly
(see `bridge/src/RenderSession.h`/`.cpp`, `bridge/src/main.cpp`).

### How the fix was verified
- Installed `gdb` (`dnf install gdb`) and ran the bridge under
  `gdb -batch -ex run -ex "thread apply all bt full"`, driven by a real
  HELLO/CREATE_SCENE/START_RENDER client, to get an actual stack trace instead
  of further guessing. This caught a *second*, unrelated issue: a defensive
  `ulimit -v 8000000` (8 GB) added for this gdb session, meant only to turn any
  further runaway allocation into a clean failure instead of a repeat VM
  incident, was itself too tight for MoonRay's legitimate 28-thread pool
  startup (`std::thread::_M_start_thread` → `pthread_create()` failing with
  `std::system_error`/`abort()` because the process had no virtual address
  space left for a new thread stack) — a resource-limit artifact of the safety
  net, not the original bug. Raising the cap to 24 GB (this workload's actual
  observed RSS is ~780 MB; MoonRay's real virtual-address reservations are
  comfortably below 24 GB) reproduced a **correct, non-crashing render** under
  gdb.
- Re-ran the full 14-check smoke suite (`bridge/tests/run_phase04_tests.py`)
  against the fixed binary: all 14 checks pass, including a full
  `CREATE_SCENE` → `START_RENDER` → shared-memory framebuffer read producing a
  512×512×4 float32 buffer with non-constant content and no NaN/Inf (see
  `smoke-test-run.txt`).
- The same 24 GB `RLIMIT_AS` cap is kept as a permanent defense-in-depth
  safety net in `bridge/tests/run_phase04_tests.py`'s `spawn_bridge()` (applied
  via a `bash -c 'ulimit -v ...; exec ...'` wrapper, not Python's
  `preexec_fn`, which proved unreliable under this session's own tool
  sandboxing) — generous enough to never constrain legitimate operation,
  tight enough that any regression of this exact bug class fails cleanly
  instead of repeating the VM-level incident.

### Deviation from a strict "never touch it once it renders" workflow
Per instruction, root causes are fixed rather than worked around. This *was*
a root-cause fix (a genuine dangling-reference bug in bridge code, not a
MoonRay defect and not a workaround) — no upstream MoonRay source was patched
and no acceptance criterion was relaxed to accommodate it.
