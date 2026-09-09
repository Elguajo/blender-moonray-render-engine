# Prior Art — MoonRay + Blender

Canonical quick reference for prior public attempts to integrate MoonRay into Blender. Full audit:
[`04-prior-blender-moonray-implementations.md`](04-prior-blender-moonray-implementations.md);
machine-readable data: [`04-prior-implementation-matrix.json`](04-prior-implementation-matrix.json).
Audited 2026-09-09.

## Most relevant prior projects

- **[`cjhosken/mfb`](https://github.com/cjhosken/mfb)** — The only prior project built on Blender's real
  `bpy.types.HydraRenderEngine` API against the real `hdMoonray` delegate. Matters because it's the closest
  thing to a serious attempt, and because its own author confirms it's currently broken, matching OpenMoonRay's
  own official statement that Blender+Hydra MoonRay rendering doesn't work yet. Has a real but functionally
  disconnected XPU execution-mode UI option, and its own build script explicitly disables OptiX
  (`-DMOONRAY_USE_OPTIX=NO`). Its `SceneVariables`-to-`PropertyGroup` mapping is a useful settings checklist
  (GPL-3.0).
- **[`cdnclass/moonray_for_blender`](https://github.com/cdnclass/moonray_for_blender)** — Earlier (2022),
  abandoned snapshot by the same author as `cjhosken/mfb` (shares initial commit history). Every render callback
  is a literal `pass`. Matters mainly as the origin point of the `mfb` lineage and as a reminder that a two-item
  CPU/GPU dropdown existing in code (here, unused/undrawn) is not evidence of anything.
- **[`HorrorPills/MoonRay-Blender-Integration`](https://github.com/HorrorPills/MoonRay-Blender-Integration)** —
  Unrelated single-session scaffold (pushed in 53 seconds) whose README/PROJECT_OVERVIEW claim far more than the
  code delivers — its `HydraRenderEngine` subclass imports a Blender module (`bl_hydra`) that does not exist and
  can never register. Matters as a cautionary example (verify source, not docs) and because its
  `material_conversion/converter.py` contains the single most genuinely useful piece of code found in this
  audit (Principled BSDF → DwaBase traversal) — but its license is unresolved (README claims Apache-2.0, no
  LICENSE file exists), so it cannot currently be reused.
- **6 known forks** (`mnraker/moonray_2_blender`, `mnraker/moonray_for_blender`,
  `SacredCodeWriter/MoonRay-Blender-Addon`, `fantomid/mfb`, `Dinesh0N/Moonray-for-Blender`,
  `SakuraEntropia/moonray_for_blender`) — All verified zero-divergence stale mirrors of the two projects above
  (`ahead_by: 0` for every one, via GitHub's compare API). None contain independent work. Matters only as a
  negative result: don't re-audit these, and don't count GitHub fork counts as adoption signal.
- **[`OpenMoonRay/openmoonray`](https://github.com/OpenMoonRay/openmoonray) Discussion #211** ("MoonRay, Blender
  and Hydra", Sept 2025) — The single most authoritative source on this whole topic: OpenMoonRay's own team,
  referencing `cjhosken/mfb` directly, states RDLA export and standalone `hd_render` work, but Hydra rendering
  inside Blender does not. Matters because it's official confirmation, independent of this audit's own code
  inspection, that nothing has ever rendered MoonRay content inside Blender.
- **AMD `BlenderUSDHydraAddon`** (reference only, not part of the MoonRay ecosystem) — A mature, working,
  GPU-accelerated Hydra-based Blender render engine addon. Matters as proof that the pattern *can* work in
  principle; MoonRay's own Hydra-Blender integration just isn't there yet.

## GPU/XPU bottom line

No project — official or third-party — has ever demonstrated MoonRay GPU/XPU rendering inside Blender. Upstream
MoonRay's own OptiX/XPU path is pinned to OptiX SDK 7.6 exactly, has documented feature gaps vs. CPU, and is
reported non-functional under WSL2 in OpenMoonRay's own community Discussions (independent of GPU hardware
capability). See the full audit's "MoonRay upstream GPU/XPU facts" and "GPU-specific risks" sections before any
future Phase touches XPU.
