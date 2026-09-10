# Phase 04 Completion — Direct MoonRay Bridge Prototype and IPC Contract

Status: COMPLETED
Completed: 2026-09-10
Workstation: `DESKTOP-9O2U790`, distro `MoonRay-Rocky9` (WSL2, Rocky Linux 9.8)

## Outcome
A minimal, crash-isolated native `moonray_bridge` process was implemented,
built against the pinned Phase 03 MoonRay/scene_rdl2 runtime, and proven to:
accept a versioned handshake over a local Unix domain socket, reject an
incompatible protocol version before any scene/render exchange, load a known
MoonRay scene (`testdata/rectangle.rdla` — the same scene Phase 03 proved
renders correctly via the `moonray` CLI) through the direct `RenderContext`
API, run a real batch render, and deliver the resulting beauty buffer to a
separate test-client process via POSIX shared memory — never through a
re-opened export file. Malformed/invalid input is rejected with structured
`ERROR` responses without corrupting the connection or the bridge process,
and a hard `SIGKILL` of the bridge process is observed by the client as a
clean connection failure with no client-side crash; a fresh bridge process on
a new socket then handles a new session normally. See
`docs/evidence/phase04/` for full observed evidence and
`docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md` for the
transport/wire-format decisions this phase made and evidenced.

## Delivered
- `bridge/src/` — the `moonray_bridge` C++ source: `main.cpp` (process
  lifecycle, connection loop, handshake enforcement), `Protocol.{h,cpp}`
  (envelope encode/decode, fixed message-type enum, per MESSAGE_SCHEMA.md),
  `PosixSocketServer.{h,cpp}` (Unix-domain-socket transport, length-prefixed
  framing), `RenderSession.{h,cpp}` (RenderContext lifecycle, batch render,
  framebuffer publish), `SharedMemoryBuffer.{h,cpp}` (POSIX shm bulk
  transport).
- `bridge/CMakeLists.txt` — builds against the Phase 03 installed runtime;
  explicitly sets `-march=core-avx2 -mavx` (MoonRay's exported CMake targets
  do not propagate this themselves — see `docs/evidence/phase04/`).
- `bridge/client/bridge_client.py` — the Phase 04 "test client" referenced by
  the phase's acceptance criteria: HELLO/CAPABILITIES/CREATE_SCENE/
  START_RENDER over the real wire protocol, plus a shared-memory framebuffer
  reader (`array.frombytes()`, not a per-pixel Python loop).
- `bridge/tests/run_phase04_tests.py` — the automated smoke test: 14 checks
  covering every acceptance-criteria bullet against the real binary and the
  real MoonRay runtime (no mocking).
- `scripts/linux/phase04_build_bridge.sh` — reproducible build script
  (mirrors `phase03_build_moonray.sh`'s dependency-hint environment variables
  and Linux-native build-directory convention).
- `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md` — records
  the transport (Unix domain socket), wire encoding (JSON via JsonCpp — an
  already-built Phase 03 transitive dependency, not a new one), and bulk-data
  path (POSIX shared memory, interleaved RGBA float32) decisions.
- `docs/evidence/phase04/` — build evidence, full smoke-test run, and a
  detailed account of a real use-after-free bug found and fixed during
  evidence-gathering.
- `docs/bridge/{PROTOCOL,MESSAGE_SCHEMA,FRAMEBUFFER_PROTOCOL,ERROR_MODEL,
  LIFECYCLE}.md` — "Decided vs. open" tables updated to close out the items
  this phase decided (wire format, IPC mechanism, bulk-data reference format,
  pixel layout, first `ERROR.code` values); items still owned by later phases
  (scene-translation field layout, incremental updates, viewport cadence,
  restart policy, etc.) remain explicitly Open.

## Observed verification
| Check | Result |
|---|---|
| `moonray_bridge` builds cleanly against the Phase 03 runtime (0 warnings, 0 errors) | PASS |
| Built binary fully resolves via `ldd` (no "not found" libraries) | PASS |
| Client can start bridge and complete a matching-version `HELLO` handshake | PASS |
| A mismatched `protocol_version` is rejected with `ERROR` category 5 and the connection is closed | PASS |
| `CAPABILITIES` returns a feature list | PASS |
| Bridge renders a known minimal scene (`testdata/rectangle.rdla`) through the direct MoonRay `RenderContext` API | PASS |
| `RENDER_COMPLETE` reports the expected 512×512×4 float32 dimensions | PASS |
| Client reads the rendered framebuffer directly from POSIX shared memory (not a re-opened export file); content is non-constant with no NaN/Inf | PASS |
| Invalid JSON body is rejected with `ERROR` category 1; connection stays open | PASS |
| Unknown message type is rejected with `ERROR` (hard error, not silently ignored); connection stays open | PASS |
| `CREATE_SCENE` with a nonexistent path is rejected with `ERROR` category 1 *before* touching native RDL2 state | PASS |
| Connection remains fully usable after all of the above malformed-input cases | PASS |
| A hard `SIGKILL` of the bridge process is observed by the client as a clean connection failure, not a hang or client-side crash | PASS |
| A fresh bridge process on a new socket handles a new session normally after the crash | PASS |
| First-run latency/memory recorded, no optimization claimed | PASS (5.47s CREATE_SCENE+START_RENDER round trip; 778 MB bridge RSS after a 512×512 single-threaded-scene render with 28 MCRT threads — see `docs/evidence/phase04/smoke-test-run.txt`) |

## Decisions made
See `docs/decisions/ADR-0004-bridge-ipc-transport-and-wire-format.md` for full
reasoning. Summary: Unix domain socket (local-only by construction), JSON
envelope via JsonCpp (already a transitive Phase 03 dependency) with a 4-byte
length-prefixed frame, and POSIX shared memory for the framebuffer (interleaved
RGBA float32, the native RDL2 `RenderBuffer` layout, published via a single
`memcpy`).

Scope decisions within the prototype itself:
- `CREATE_SCENE` loads a full `.rdla` scene file path rather than implementing
  any canonical mesh/camera/material bridge schema — full scene/material
  translation is explicitly Phase 06/07 scope; Phase 04 only needed to prove
  the render pipeline end-to-end through a *known-good* scene.
- Only `render_mode: "final"` (synchronous BATCH) is implemented;
  `"viewport"`/`"animation"` are recognized values that return an explicit
  `ERROR` category 2 (`UNSUPPORTED_FEATURE`) rather than being silently
  accepted — progressive/animation render modes are Phase 08/09 scope.
- `STOP_RENDER`/`UPDATE_OBJECT`/`UPDATE_CAMERA`/`UPDATE_MATERIAL` are part of
  the fixed message-type enum (so an unknown-type hard-error check has
  something real to distinguish against) but return `ERROR` category 2
  (`NOT_IMPLEMENTED_PHASE04`) rather than being implemented — each is owned by
  a later phase (06/07/08).
- One client connection at a time; no concurrency support in this phase (not
  required by any acceptance criterion, and the add-on is the bridge's only
  intended client).

## Problems discovered and fixed
1. **MoonRay's exported CMake targets do not propagate their own required ISA
   compile flags.** Confirmed exactly as flagged going into this phase:
   compiling against the installed headers without `-march=core-avx2 -mavx`
   fails with `avxintrin.h: '__builtin_ia32_ps256_ps' was not declared in this
   scope`. Fixed by setting these flags explicitly in `bridge/CMakeLists.txt`
   (MoonRay itself sets them via `cmake_modules/cmake/MoonrayDso.cmake`, which
   is not visible to a downstream consumer's own targets). Zero warnings/errors
   afterward. This raises the bridge's own minimum CPU requirement to
   AVX2/`core-avx2`, matching MoonRay's own.
2. **`-DCMAKE_PREFIX_PATH` passed as a `-D` cache variable silently failed to
   resolve `SceneRdl2Config.cmake`**, even though the identical colon-joined
   path string worked when exported as an environment variable in
   `phase03_build_moonray.sh`. Root cause: CMake only splits the *environment
   variable* form of `CMAKE_PREFIX_PATH` on the OS path-list separator (`:` on
   Linux); a `-D` cache variable requires `;`. Fixed
   `scripts/linux/phase04_build_bridge.sh` to `export` it instead of passing
   `-D`, and to export the same `*_ROOT`/`CMAKE_MODULES_ROOT`/`ISPC` hint
   variables `phase03_build_moonray.sh` uses — `SceneRdl2Config.cmake`'s own
   `find_dependency()` calls (CppUnit, JsonCpp, Log4cplus, Lua, OpenSubdiv,
   OpenVDB, Random123) need them regardless of `CMAKE_PREFIX_PATH`.
3. **A genuine use-after-free crash**, found and root-caused during
   evidence-gathering, not merely worked around: `RenderContext` stores its
   `RenderOptions` constructor argument by reference
   (`RenderOptions& mOptions;`), and the bridge's first implementation passed
   a function-local `RenderOptions` that was destroyed while the
   longer-lived `RenderContext` still referenced it. The crash was
   perfectly reproducible (same scene, same stack layout each run) and its
   symptom — MoonRay's arena allocator reporting individual allocation
   requests in the hundreds-of-GB to multi-TB range — is consistent with
   reading deterministic stack garbage as a `RenderOptions` object. Kernel
   log evidence (`dmesg`) recorded a fault register dump and, on a later
   attempt, a fresh WSL boot sequence — consistent with, though not
   conclusively isolated to, this bug having destabilized the WSL2 VM itself,
   not just the one process. Fixed by giving `main()` a single process-wide
   `RenderOptions`, passed by reference into both `initGlobalDriver()` and
   every `RenderSession`/`RenderContext`, matching the reference
   implementation (`moonray/cmd/raas_cmd/moonray/moonray.cc`) exactly. Full
   root-cause account, including a secondary diagnostic-tooling artifact this
   investigation also had to distinguish from the real bug (an overly tight
   `ulimit -v` safety cap producing an unrelated, expected thread-creation
   failure), is in `docs/evidence/phase04/README.md`. Verified fixed: the
   full 14-check smoke suite now passes with a correct, non-crashing,
   non-constant render.
4. **Cold-start timing variance.** The bridge's first-ever launch after a
   fresh build took ~16s to reach "listening" (MoonRay global-driver/
   thread-pool initialization, `initGlobalDriver()`); a subsequent warm
   launch took ~1.2s. The test harness's launch-timeout was raised from an
   initial too-tight 5s to 40s to tolerate this without weakening any
   acceptance check.

## Deviations / technical debt
- A defensive 24 GB `RLIMIT_AS` cap was added to the test harness's bridge
  launch (`bridge/tests/run_phase04_tests.py`) as defense-in-depth against a
  regression of problem #3 above; it is generous enough to never constrain
  this workload's legitimate ~780 MB RSS and is not a production packaging
  decision — Phase 11 owns any real resource-limit policy.
- Shared-memory segment cleanup is session-scoped only (the bridge unlinks
  the previous render's segment when starting the next, and on clean
  shutdown); see ADR-0004 "Costs / open follow-ups" for the acknowledged gap
  (a crashed-and-never-reconnected session could leak one segment).
- No concurrent-client support, no socket-path collision guard between two
  bridge instances — both explicitly out of Phase 04 scope per
  `docs/phases/04-direct-bridge-prototype.md` ("Full Blender integration",
  "Production viewport performance", "Distributed networking" are out of
  scope; concurrency was never an acceptance criterion).
- `STOP_RENDER`/`UPDATE_OBJECT`/`UPDATE_CAMERA`/`UPDATE_MATERIAL` remain
  unimplemented placeholders (explicit `ERROR` category 2), as scoped.

## Architectural impact
ADR-0004 added (bridge IPC transport, wire format, bulk-data path) — a new
decision filling in mechanics ADR-0002 deliberately left open, not a change to
ADR-0002 itself. ADR-0002 (Direct MoonRay Bridge primary; Hydra/hdMoonray
reference-only) is otherwise unaffected — Hydra/hdMoonray was never built or
touched.

## GPU/XPU status carried forward
Unchanged from Phase 03: CPU is the only proven render path. The bridge links
the same `-DMOONRAY_USE_OPTIX=NO` runtime Phase 03 built; no GPU/XPU
capability is claimed or implied by this phase.

## Follow-up
Phase 05: Blender `RenderEngine` integration and first F12 MoonRay frame,
launching/version-checking this `moonray_bridge` process from the add-on and
driving it over the protocol this phase implemented. Not started by this
phase.
