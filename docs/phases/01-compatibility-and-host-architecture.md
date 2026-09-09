# Phase 01 — Current Compatibility Research and Host Architecture Decision

## Goal
Produce a source-backed compatibility matrix and select one production architecture for Blender 5.2+ + MoonRay on a Windows-hosted workstation without writing a new renderer integration.

## Context
The user explicitly accepted WSL2 as the execution boundary. Research then validated the compatibility contract and selected the detailed stack.

## Context hints
- `docs/project/PROJECT_BRIEF.md`
- `docs/project/ARCHITECTURE.md`
- `docs/research/01-compatibility-matrix.md`
- `docs/decisions/ADR-0001-wsl2-linux-blender-hydra-host.md`

## In scope
- Verify current Blender 5.2+ Hydra/OpenUSD integration details.
- Verify current MoonRay and hdMoonray supported operating systems, build requirements and Hydra/USD expectations.
- Inspect maintained/available Blender-MoonRay community integrations and their exact compatibility assumptions.
- Verify WSL2/WSLg GPU/GUI viability at platform level.
- Compare native Windows Blender, Linux Blender under WSL2/WSLg, and dedicated Linux fallback.
- Select one primary architecture and fallback hierarchy.
- Record version constraints and unresolved blockers.

## Out of scope
- Installing the full stack.
- Compiling MoonRay.
- Patching community integration code.
- Production performance benchmarking.

## Tasks
- [x] Gather current primary-source compatibility evidence.
  - Result: current Blender, MoonRay, hdMoonray, Microsoft WSL and NVIDIA WSL/CUDA sources are recorded in `docs/research/01-compatibility-matrix.md`.
- [x] Build component/version/OS compatibility matrix.
  - Result: native Windows = FAIL; WSL2 Linux host = selected conditional PASS; Blender/USD/hdMoonray ABI coupling explicitly documented.
- [x] Evaluate architecture options against must-have workflow.
  - Result: WSL2/WSLg Linux Blender selected; dedicated Linux retained as platform fallback; batch USD retained diagnostic-only.
- [x] Record consequential decision as ADR.
  - Result: `docs/decisions/ADR-0001-wsl2-linux-blender-hydra-host.md` accepted.
- [x] Update Architecture with selected path and fallback.
  - Result: architecture now pins the WSL2 boundary, Blender 5.2.1 baseline, Blender-host USD contract, hdm_10 candidate and CPU-first rollout.

## Acceptance criteria
- [x] Every material compatibility claim is backed by a current primary source or explicitly marked unknown.
- [x] A concrete primary architecture is selected for implementation.
- [x] Native Windows feasibility is explicitly PASS / FAIL / UNKNOWN with reason.
- [x] Blender 5.2+ compatibility risk is explicit rather than inferred from Blender 4.x.
- [x] Required version pins/build coupling for OpenUSD/Hydra/hdMoonray are identified as far as available evidence permits.
- [x] A fallback architecture exists if the primary path fails in Phase 04.

## Negative / security cases
- Current community addon README claims were not accepted as proof of Blender 5.2 compatibility.
- No third-party binaries were downloaded or executed in this research phase.
- Batch-only USD rendering remains diagnostic-only and is not represented as equivalent to an in-Blender Render Engine.

## Verification
- Primary source set reviewed on 2026-09-08.
- Compatibility matrix checked against Project Brief must-haves.
- Blender 5.2 source dependency configuration checked for OpenUSD version and internal namespace behavior.
- Current hdm_10 branch CMake checked for its USD minimum and current Hydra 2.0 branch status.
- Community addon source/README inspected to distinguish marketing/intent from actual readiness.

## Completion Record
Status: COMPLETED
Completed: 2026-09-08
Final report: `docs/completions/01-compatibility-and-host-architecture.md`

Outcome: WSL2/WSLg with Linux Blender was accepted and validated as the primary platform architecture. The critical implementation constraint is now explicit: hdMoonray must be built against Blender's host-compatible OpenUSD/Hydra ABI, not an arbitrary standalone USD. Blender 5.2.1 LTS is the initial host baseline; hdm_10 is the preferred Hydra 2.0 delegate candidate; MoonRay 2026.29.1 is the initial renderer baseline.

Validation summary: source-backed matrix complete; native Windows path rejected; WSL2 selected; ABI fallback and dedicated-Linux fallback recorded.

Technical debt / next-phase risks: custom Rocky Linux 9 WSLg behavior and actual workstation GPU visibility are not yet verified; hdMoonray 10 against Blender USD 26.03 remains unproven; XPU remains a separate risk gate.

Handoff: Phase 02 must establish the WSL2/Rocky9/WSLg/Blender 5.2.1 host foundation only. Do not build MoonRay until Phase 02 passes.

## Later architecture change
ADR-0002 (2026-09-09) supersedes the Hydra/hdMoonray **primary integration** decision. The Phase 01 host/compatibility research remains historical evidence; WSL2 host selection remains accepted.
