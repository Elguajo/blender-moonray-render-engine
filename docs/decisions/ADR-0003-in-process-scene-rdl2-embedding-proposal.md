# ADR-0003 — In-process scene_rdl2 embedding via Python bindings (rejected)

Status: **REJECTED — deferred to ADR-0002's own revisit trigger**
Date: 2026-09-09
Relates to: ADR-0002 (remains authoritative; this ADR does not supersede it)

## Decision record
The user asked for a recommendation on Option 1/2/3 below rather than deciding directly, then
asked for direct empirical comparison against two production renderers (V-Ray, Octane)
installed locally before finalizing. Applying the analysis in this document, now backed by
that comparison (see "Evidence from comparable production Blender integrations" below):
**Option 1 (defer)**. `moonray_bridge` stays C++, out-of-process, per ADR-0002. No files
outside this ADR change. This option will be revisited only if one of ADR-0002's own revisit
triggers actually fires (most likely: Phase 04 transport-overhead measurements come in
unacceptable, or Phase 10 benchmark evidence points
this way) — not speculatively.

## Context
ADR-0002 chose an out-of-process `moonray_bridge` (C++, owns MoonRay/scene_rdl2 natively)
specifically to avoid loading MoonRay's native dependency graph into Blender's own process
before any performance evidence existed. `PROJECT_BRIEF.md` states this as an explicit
constraint: *"Do not embed MoonRay libraries into Blender's process as the first production
architecture; in-process integration requires later profiling + ABI/crash-risk
justification"* and lists *"In-process integration solely for theoretical speed without
measured bridge bottleneck"* as out of scope for the first release. ADR-0002 itself rejected
it the same way: *"In-process MoonRay library on day one: rejected due crash/ABI risk before
performance evidence."*

This proposal originates from research requested by the user into a third-party project —
[OpenMoonRay discussion #223](https://github.com/OpenMoonRay/openmoonray/discussions/223),
[alanblevins/scene_rdl2_pybind11](https://github.com/alanblevins/scene_rdl2_pybind11) — which
wraps scene_rdl2 with pybind11 (its own author: a Claude Code learning exercise, explicitly
"not for production," macOS-only). That research also surfaced that scene_rdl2 already ships
official `boost::python` bindings upstream (`mod/python/py_scene_rdl2`). The user then asked
to re-evaluate whether Blender should load scene_rdl2 **in-process**, via either binding set,
instead of the out-of-process C++ bridge.

**No new evidence exists to satisfy ADR-0002's own revisit bar.** Phase 03 (native MoonRay
runtime) has not started; nothing has been built or benchmarked locally; there is no bridge
prototype to compare a transport-overhead measurement against. This ADR is being written
because the user explicitly asked to reconsider it, not because a revisit trigger fired.

## What "in-process" would actually mean
Either binding set (`boost::python` or the community `pybind11`/`nanobind` code) is a thin
compiled wrapper — accepting it does not avoid the underlying risk ADR-0002 was written
around, because the wrapped native code is the same MoonRay/scene_rdl2 dependency graph
(TBB, OpenImageIO, OpenEXR/Imath, Embree, MoonRay's shader/geometry DSO plugin loader) now
resident inside Blender's own process address space instead of an isolated one.

Concrete new risks this reintroduces, specific to this project's stack (not generic
doctrine):
- **Crash isolation is lost.** A native fault anywhere in MoonRay/scene_rdl2/Embree/a loaded
  DSO now crashes Blender itself and the `.blend` session. `PROJECT_BRIEF.md`'s success
  criterion *"Blender survives bridge-process failure"* becomes structurally unsatisfiable —
  there is no separate process left to fail.
- **Python ABI must match Blender's exact bundled interpreter.** Phase 02 evidence records
  Blender 5.2.1 LTS ships **Python 3.13.13** (`docs/project/NEXT_SESSION.md`). Both binding
  sets are compiled extensions tied to one exact CPython build; the community repo was built
  against Homebrew Python 3.13 on macOS arm64, not Blender's bundled interpreter, and not on
  our Rocky Linux 9 target — none of its build output is usable as-is.
- **Symbol/library version skew with Blender's own native deps.** Blender already links its
  own copies of OpenImageIO/OpenEXR/TBB internally (for Cycles/image IO). Loading scene_rdl2's
  copies into the same process risks duplicate-symbol or ABI-version conflicts that an
  out-of-process boundary sidesteps entirely — this is the exact concern ADR-0002 names
  ("MoonRay and Blender carry large native dependency graphs... can create symbol/ABI
  conflicts").
- **GIL/threading discipline becomes the project's problem.** MoonRay's TBB-driven render
  loop would need explicit GIL release (`py::gil_scoped_release` or equivalent) around every
  long-running native call to avoid freezing Blender's UI during progressive/interactive
  rendering — solvable, but new complexity with no current design coverage.
- **DSO loading adds more in-process surface.** scene_rdl2 dynamically loads shader/geometry
  DSOs at runtime via `RDL2_DSO_PATH`; each loaded DSO is itself native code sharing the same
  process, compounding the ABI-conflict surface rather than isolating it.
- **New packaging/maintenance burden.** Prebuilt bindings would need rebuilding against every
  Blender Python point-release the project supports, versus the current design where only the
  bridge's own IPC protocol version needs to match.

None of this makes in-process embedding impossible — it may be a reasonable choice once there
is a working bridge to measure against. It does mean nothing available today (a macOS hobby
project by someone outside this project, built as an AI-pairing exercise and explicitly
disclaimed for production use) constitutes the "profiling + ABI/crash-risk justification"
`PROJECT_BRIEF.md` itself sets as the bar for revisiting this.

## Evidence from comparable production Blender integrations
At the user's request, two commercial third-party renderers installed on the user's own
workstation were inspected directly (add-on source under
`%APPDATA%\Blender Foundation\Blender\`, and the vendor install trees under
`C:\Program Files\`) to see how production-grade renderers actually solve this, rather than
reasoning about it in the abstract.

**V-Ray for Blender (Chaos), installed build, `vray_blender` add-on source
(`engine/zmq_process.py`):** confirmed out-of-process. The add-on is pure Python; on render
start it launches a separate `VRayZmqServer.exe` process (`_startServerProcess()`), passes it
`args.blenderPID = os.getpid()` so the server can track the parent Blender process, and talks
to it only through a thin compiled control-channel client (`VRayBlenderLib`, imported as
`vray`) over what the module name (`zmq_process.py`) identifies as a ZeroMQ-based channel.
Crash handling is explicit and user-facing: `_zmqServerAbortCallback` detects
`"General error"/"STD exception"/"V-Ray exception"/"Unknown error"` from the server and
reports *"Restart is required! V-Ray internal error occurred"* — Blender itself keeps running.
This is structurally the same shape as `moonray_bridge` + IPC in ADR-0002: thin Python
orchestration in Blender's process, the actual renderer isolated in its own process, explicit
PID-tracked lifecycle and crash recovery.

**Octane (OTOY), installed build `OctaneBlender30.11.0` +
`OctaneServerPrime30.11\OctaneServer.exe`:** also client-server, though packaged differently.
OTOY ships a custom-built Blender executable (their own `blender.exe`/bundled Python) rather
than a plain add-on for a stock Blender, and its default configuration
(`ENABLE_OCTANE_ADDON_CLIENT = False` in `octane/core/__init__.py`) loads a module named
`_octane` **compiled directly into that custom Blender build** — which looks, on the surface,
like the in-process embedding this ADR is about. But the same file labels that exact
configuration *"Octane Custom-Build **Client** is enabled"*, sets
`OCTANE_MODULE_SERVER_MODE = True`, and the actual scene/render API it wraps lives in
`octane.core.client.OctaneBlender`, whose methods (`update_server_settings(...)`,
`start_render(...)`) talk to the separate `OctaneServer.exe` process found alongside it on
disk. In other words: even OTOY's tightest, custom-Blender-build integration keeps the actual
renderer (GPU kernels, scene graph, device management) in its own process; only a thin RPC
client stub is compiled into the Blender executable instead of loaded as a dynamic library.
They do not embed the renderer itself in-process either.

**Reading:** two of the most mature commercial Blender renderer integrations that exist both
converge on "renderer lives in its own process, Blender talks to it as a client" as the
production answer — not as a first-draft simplification later replaced by something in-process,
but as their shipping, current architecture. Neither supports treating in-process embedding as
the industry-standard or lower-risk default; if anything this is independent, unsolicited
confirmation that ADR-0002's out-of-process design is the well-trodden path here, and that even
vendors with far more resources than this project (custom Blender builds, GPU driver-level
integration needs) still pay the IPC cost rather than accept the crash/ABI exposure of true
in-process embedding.

## Options
1. **Defer (recommended).** Keep this ADR as a recorded, PROPOSED option; revisit for real at
   Phase 10 (or earlier if Phase 04 IPC-overhead measurements come in unacceptable), per
   ADR-0002's own revisit trigger — *"If Phase 10 proves transport to be the dominant
   bottleneck, an in-process variant may be evaluated under a new ADR."* No files outside this
   ADR change; `moonray_bridge` stays C++, out-of-process, as planned.
2. **Accept now, pre-evidence.** Explicitly override ADR-0002/`PROJECT_BRIEF.md`'s in-process
   constraint on the user's authority alone, without the profiling those documents call for.
   If chosen, this ADR's status becomes ACCEPTED and supersedes ADR-0002's out-of-process
   decision; `ARCHITECTURE.md`, `PROJECT_BRIEF.md`, `docs/project/ROADMAP.md` and
   `AGENT_HANDOFF.md` all need corresponding updates (bridge process shape, Phase 03/04
   scope, crash-isolation success criterion either dropped or redefined), and Phase 03/04
   plans would need to be re-scoped around building/matching Blender's bundled Python instead
   of a standalone C++ runtime.
3. **Reject.** Record that in-process was considered and explicitly not pursued; no changes
   elsewhere.

## Recommendation
Option 1 (defer). The case for reconsidering right now rests on one non-production,
macOS-only, third-party learning project plus the fact that scene_rdl2 has *some* official
Python bindings — neither is evidence about crash risk, ABI compatibility with Blender's
bundled Python 3.13.13, or performance on this project's actual Rocky Linux 9 target.
Accepting now would reverse a deliberate, documented decision on weaker evidence than the
project's own stated bar for reversing it.

## Consequences if left PROPOSED (not accepted)
- No change to current architecture, roadmap, or phase scope.
- The option is preserved and discoverable for Phase 10 (or an earlier evidence-driven
  trigger) instead of being silently forgotten.
