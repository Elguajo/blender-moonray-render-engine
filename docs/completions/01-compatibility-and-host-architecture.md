# Phase 01 Completion — Current Compatibility Research and Host Architecture Decision

Status: COMPLETED
Completed: 2026-09-08

## Outcome
A source-backed production architecture was selected for running MoonRay as a Blender 5.2+ render engine on a Windows workstation: Linux Blender inside WSL2/WSLg, with hdMoonray built against Blender's exact host-compatible OpenUSD/Hydra environment.

## Delivered
- Compatibility matrix: `docs/research/01-compatibility-matrix.md`.
- Accepted architecture decision: `docs/decisions/ADR-0001-wsl2-linux-host-boundary.md`.
- Updated canonical architecture: `docs/project/ARCHITECTURE.md`.
- Initial frozen host baseline: Blender 5.2.1 LTS.
- Preferred delegate line: HdMoonray 10 (`hdm_10`) because it targets Hydra 2.0 clients.
- Initial renderer release baseline: MoonRay 2026.29.1.
- CPU-first / XPU-later validation policy.
- Explicit fallback hierarchy.

## Implementation notes
Blender 5.2's source configuration pins OpenUSD 26.03 and builds it with an internal namespace derived as `pxrBlender_v${USD_VERSION}`. This is materially important because MoonRay upstream guidance says a Hydra DCC plugin must build/link against the USD used by the host DCC; binary-incompatible USD versions can crash.

HdMoonray 10 was announced on 2026-08-28 as DreamWorks' Hydra 2.0-capable line and is the best architectural match for Blender 5.2's Hydra 2.0 implementation. However, its announced validation uses USD 0.25.5, while Blender 5.2 uses USD 26.03. Its CMake currently requires PXR >= 25.05 rather than rejecting newer USD, so 26.03 is a build candidate but not a verified runtime combination.

Existing Blender-MoonRay community projects do not provide a production-ready Blender 5.2 solution as-is. `cjhosken/mfb` explicitly marks itself broken. The inspected `HorrorPills/MoonRay-Blender-Integration` engine code does not match the current Blender 5.2 HydraRenderEngine API contract and contains placeholder generic-render-engine behavior. Both remain useful as reference material only.

## Decisions made
- WSL2/WSLg is the accepted execution boundary; see ADR-0001.
- Rocky Linux 9 is the target distro because MoonRay currently tests it upstream; actual WSLg behavior is a Phase 02 validation item.
- Blender 5.2.1 LTS is frozen as the first integration baseline.
- Do not use native Windows Blender for the MoonRay integration while upstream MoonRay lacks supported native Windows builds.
- Treat Blender's USD build as the delegate SDK/ABI owner.
- CPU rendering is the first required success criterion; XPU is additive and separately validated.

## Deviations / technical debt
- No installation/build was performed by design.
- Exact hdm_10 commit is deferred until immediately before the Phase 03 build so the source pin reflects the implementation baseline.
- Exact Rocky Linux 9 point release, WSL version, Windows build and GPU/driver versions are deferred to Phase 02 inventory.

## Problems discovered
- The largest risk is not WSL itself but Blender/OpenUSD/hdMoonray binary compatibility.
- Blender's custom OpenUSD internal namespace means merely matching the numeric USD version may be insufficient.
- WSL CUDA documentation lists unsupported OpenGL-CUDA interop and memory limitations; MoonRay XPU therefore cannot be assumed production-safe without testing.

## Verification evidence
- Blender official release pages → Blender 5.2.1 LTS is current on 2026-09-08 and supported to July 2028.
- Blender 5.2 developer notes → Hydra implementation uses Hydra 2.0.
- Blender 5.2 source dependency config → OpenUSD 26.03 plus Blender-specific internal namespace setup.
- MoonRay official build docs → Linux/macOS support and Rocky Linux 9 testing.
- MoonRay discussion #125 → DCC Hydra plugin should build/link against the host DCC's USD to avoid binary incompatibility.
- MoonRay discussion #270 → hdm_10 is the Hydra 2.0-capable HdMoonray line, tested upstream with USD 0.25.5.
- hdm_10 CMake → minimum PXR 25.05; newer 26.03 is not rejected at configure-policy level.
- Microsoft WSL docs → Linux GUI apps/WSLg/vGPU path supported on Windows 11.
- NVIDIA WSL docs → CUDA apps can run/build in WSL2, with documented feature limitations.

## Architectural impact
Later phases may assume WSL2 is the primary execution boundary and should not spend work on a native Windows MoonRay port. They must preserve the host-USD ABI rule and version pins.

## Follow-up
Phase 02: create and verify the WSL2/Rocky Linux 9/WSLg/Blender 5.2.1 foundation, inventory the actual workstation, test GUI/GPU visibility, and record reproducible environment state. No MoonRay compilation yet.

## Later architecture change
ADR-0002 (2026-09-09) supersedes the Hydra/hdMoonray **primary integration** decision. The Phase 01 host/compatibility research remains historical evidence; WSL2 host selection remains accepted.
