# Research 05 — Applied Harvest from Prior Blender↔MoonRay Implementations

Harvest date: **2026-09-10**. Purpose: extract *concrete, reusable specifics* from the two prior public
implementations for **Phase 06** (geometry/camera/lights), **Phase 07** (materials/textures/instances) and
**Phase 08** (interactive viewport).

This document **does not repeat** the inventory audit in
[`04-prior-blender-moonray-implementations.md`](04-prior-blender-moonray-implementations.md),
[`PRIOR_ART.md`](PRIOR_ART.md) and [`04-prior-implementation-matrix.json`](04-prior-implementation-matrix.json).
Those established *who wrote what, that all six forks are zero-divergence mirrors, and that nothing ever rendered
a MoonRay frame inside Blender*. All of that is taken as given here. This document answers a narrower question:
**what, line by line, is worth taking, and what will actively mislead us.**

No phase was activated by this work. No code under `addon/` or `bridge/` was changed. Nothing from either
third-party repository was built, installed or executed; both were cloned read-only into the session scratchpad
and read as source text.

---

## 0. Sources, verification state, and method

### Repositories read (full source, not READMEs)

| Repo | Clone HEAD at harvest time | HEAD date | Files read |
|---|---|---|---|
| [`cjhosken/mfb`](https://github.com/cjhosken/mfb) | `b0b17cfe56e84cde62363d7ad44b5bc60ec91b0b` ("attempted build (still failing)") | 2026-07-16 | all 41 tracked text files (5 346 Python lines) |
| [`HorrorPills/MoonRay-Blender-Integration`](https://github.com/HorrorPills/MoonRay-Blender-Integration) | `0b5572302bceb1a1fd03429d8a4174afb2dd0aa6` ("Created Repo") | 2026-02-09 | all 15 tracked files (1 399 Python lines) |

`cdnclass/moonray_for_blender` was not re-read: research 04 established it shares initial-commit history with
`cjhosken/mfb` and that all of its render callbacks are literal `pass`; nothing in the sections below depends on
it. Forks were not touched (confirmed zero-divergence in research 04).

`HorrorPills/…` has exactly **two commits, 53 seconds apart** (`git log`: `5db2eabe` 2026-02-09 19:22:06 +0100,
`0b557230` 2026-02-09 19:22:59 +0100) — research 04's single-session finding is confirmed at source level.

### Upstream ground truth used for every cross-check

Claims about "what MoonRay actually has" below are taken **from source at the commits pinned in
[`UPSTREAM_LOCK.json`](../../UPSTREAM_LOCK.json)**, never from documentation:

| Artifact | Pinned commit | Fetched file(s) |
|---|---|---|
| `scene_rdl2` | `1229d3eaa1ee41dc1ddefbe781c623edceafbac8` | `lib/scene/rdl2/SceneVariables.{h,cc}`, `Camera.cc`, `Node.cc`, `Geometry.cc` |
| `moonray` | `eef67ae992b5037943a7716cca96ed443c36dcec` | `dso/geometry/RdlMesh/attributes.cc`, `dso/geometry/RdlInstancerGeometry/attributes.cc`, `dso/camera/PerspectiveCamera/attributes.cc`, full recursive tree listing (1 727 entries) |
| `moonshine` | `a3c8667298a23df7d6efed128cb475484de66c8e` | `dso/material/DwaBase/DwaBaseMaterial.json` + all 24 `lib/material/dwabase/json/*.json` includes |
| `blender` | `9e2066aef7ef7e20c142ad7bd3303138a4304c93` (v5.2.1) | `source/blender/nodes/shader/nodes/node_shader_bsdf_principled.cc` |

Line numbers cited as `SceneVariables.cc:NNN` etc. refer to these exact commits.

### License state re-verified live (2026-09-10)

`gh api repos/cjhosken/mfb` → `license.spdx_id = "GPL-3.0"`; `LICENSE.txt` present in the clone (620 lines,
verbatim GPLv3 text, **no filled-in copyright line**, no per-file headers in any `.py`).

`gh api repos/HorrorPills/MoonRay-Blender-Integration` → **`license: null`**; root listing via the contents API
returns only `PROJECT_OVERVIEW.md README.md addon build_scripts docs material_conversion tests` — **still no
LICENSE file**, while `README.md:26` and `README.md:276` continue to claim "Apache 2.0". Research 04's finding is
unchanged as of today. See §6.

---

## 1. `SceneVariables` → Blender `PropertyGroup`: what `cjhosken/mfb` actually covers

### 1.1 Headline numbers

| Measure | Count | Source |
|---|---|---|
| `SceneVariables` attributes declared upstream | **118** | `SceneVariables.cc` @ `1229d3ea`, `declareAttribute` occurrences |
| Blender properties declared in mfb's `SceneVariables` groups | **108** | `props/attributes.py`, 19 `PropertyGroup` classes |
| Of those, actually **drawn in any panel** | **70** (38 never drawn) | `ui/mfb_render.py`, `ui/mfb_output.py`, `preferences.py` |
| Keys in `MoonRayRenderEngine.get_render_settings()` | **106** `sceneVariable:*` | `engine/__init__.py:43-206` |
| Of those keys whose value comes from the user's `PropertyGroup` | **0** | see §1.2 |

**mfb's `SceneVariables` coverage is ~92 % by name and 0 % by data flow.** That is the single most important
finding of this section, and the reason this is a *coverage checklist*, not portable code.

### 1.2 The PropertyGroups are wired to nothing

`engine/__init__.py:41` reads `moonray = bpy.context.scene.moonray`, and then **never uses `moonray` again**.
Every value in the returned dict (`engine/__init__.py:43-206`) is a hard-coded literal. `pixel_samples` is
always `8`, `max_depth` always `5`, `enable_dof` always `True`, regardless of what the user set in the panels
that `props/attributes.py` + `ui/*.py` so carefully build.

Consequence for us: **do not treat mfb's dict as an "IPC payload shape" that was ever exercised.** It is an
un-run literal. Its value is purely the *name list* and the *inline enum comments* (`engine/__init__.py:73,79,
109,124,126,149,170,173-176`), which are transcriptions of upstream enum meanings and match what
`setEnumValue` declares (verified: `sampling_mode` 0=uniform/2=adaptive `SceneVariables.cc:305-306`;
`pixel_filter` 0/1/2 = box/cubic b-spline/quadratic b-spline `:604-606`; the nine tile orders `:958-975`).

### 1.3 Full coverage table

Legend for the last column: cross-check is against `scene_rdl2` `SceneVariables.cc` at pinned commit
`1229d3eaa1ee41dc1ddefbe781c623edceafbac8`. "**ABSENT**" means the name does not exist upstream at that commit.

**`MoonRayAttributes_Caching`** -> `scene.moonray.caching`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `fast_geometry_update` (L10) | `BoolProperty` | `False` | Add-on Preferences (`preferences.py`:30) | yes | `Bool`, default `false` (L676) |
| `texture_cache_size` (L12) | `IntProperty` | `4000` | Add-on Preferences (`preferences.py`:31) | yes | `Int`, default `Int(4000)` (L653) |
| `texture_file_handles` (L13) | `IntProperty` | `24000` | Add-on Preferences (`preferences.py`:32) | yes | `Int`, default `Int(24000)` (L670) |

**`MoonRayAttributes_CameraAndLayer`** -> `scene.moonray.camera_and_layer`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `camera` (L18) | `PointerProperty` | `(none)` | **never drawn** | **no** | `SceneObject*`, default `FLAGS_NONE` (L194) |
| `dicing_camera` (L25) | `PointerProperty` | `(none)` | **never drawn** | yes | `SceneObject*`, default `FLAGS_NONE` (L200) |
| `layer` (L33) | `PointerProperty` | `(none)` | **never drawn** | **no** | `SceneObject*`, default `FLAGS_NONE` (L206) |

**`MoonRayAttributes_Checkpoint`** -> `scene.moonray.checkpoint`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `checkpoint_active` (L41) | `BoolProperty` | `False` | Output props (`ui/mfb_output.py`:23) | yes | `Bool`, default `false` (L685) |
| `checkpoint_bg_write` (L42) | `BoolProperty` | `True` | Output props (`ui/mfb_output.py`:27) | yes | `Bool`, default `true` (L759) |
| `checkpoint_interval` (L43) | `FloatProperty` | `15.0` | Output props (`ui/mfb_output.py`:28) | yes | `Float`, default `Float(15.0f)` (L692) |
| `checkpoint_max_bgcache` (L44) | `IntProperty` | `2` | Output props (`ui/mfb_output.py`:29) | yes | `Int`, default `Int(2)` (L791) |
| `checkpoint_max_snapshot_overhead` (L46) | `FloatProperty` | `2.0` | Output props (`ui/mfb_output.py`:30) | yes | `Float`, default `Float(0.0f)` (L801) |
| `checkpoint_mode` (L47) | `EnumProperty` | `"0"` | Output props (`ui/mfb_output.py`:31) | yes | `Int`, default `Int(0)` (L738) |
| `checkpoint_overwrite` (L57) | `BoolProperty` | `True` | Output props (`ui/mfb_output.py`:32) | yes | `Bool`, default `true` (L730) |
| `checkpoint_post_script` (L58) | `StringProperty` | `""` | Output props (`ui/mfb_output.py`:33) | yes | `String`, default `""` (L767) |
| `checkpoint_quality_steps` (L59) | `IntProperty` | `2` | Output props (`ui/mfb_output.py`:34) | yes | `Int`, default `Int(2)` (L700) |
| `checkpoint_sample_cap` (L60) | `IntProperty` | `0` | **never drawn** | yes | `Int`, default `Int(0)` (L722) |
| `checkpoint_snapshot_interval` (L61) | `FloatProperty` | `0.0` | Output props (`ui/mfb_output.py`:36) | yes | `Float`, default `Float(0.0f)` (L812) |
| `checkpoint_start_sample` (L62) | `IntProperty` | `1` | Output props (`ui/mfb_output.py`:37) | yes | `Int`, default `Int(1)` (L752) |
| `checkpoint_time_cap` (L63) | `FloatProperty` | `0.0` | Output props (`ui/mfb_output.py`:38) | yes | `Float`, default `Float(0.0f)` (L714) |
| `checkpoint_total_files` (L64) | `IntProperty` | `0` | Output props (`ui/mfb_output.py`:39) | yes | `Int`, default `Int(0)` (L776) |

**`MoonRayAttributes_Debug`** -> `scene.moonray.debug`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `debug_console` (L67) | `IntProperty` | `-1` | Add-on Preferences (`preferences.py`:20) | yes | `Int`, default `Int(-1)` (L1128) |
| `debug_pixel` (L68) | `IntVectorProperty size=2` | `(0, 0)` | Add-on Preferences (`preferences.py`:21) | yes | `IntVector`, default `debugPixel` (L1120) |
| `validate_geometry` (L70) | `BoolProperty` | `False` | Add-on Preferences (`preferences.py`:22) | yes | `Bool`, default `false` (L1140) |

**`MoonRayAttributes_DeepImages`** -> `scene.moonray.deep_images`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `deep_curvature_tolerance` (L73) | `FloatProperty` | `45.0` | **never drawn** | yes | `Float`, default `Float(45.0)` (L627) |
| `deep_id_attribute_names` (L84) | `CollectionProperty` | `(none)` | **never drawn** | yes | `StringVector`, default `{"deep ID attribute names"}` (L647) |
| `deep_vol_compression_res` (L85) | `IntProperty` | `10` | **never drawn** | yes | `Int`, default `Int(10)` (L640) |
| `deep_z_tolerance` (L86) | `FloatProperty` | `2.0` | **never drawn** | yes | `Float`, default `Float(2.0)` (L633) |

**`MoonRayAttributes_Driver`** -> `scene.moonray.driver`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `machine_id` (L90) | `IntProperty` | `-1` | Add-on Preferences (`preferences.py`:25) | yes | `Int`, default `-1` (L932) |
| `num_machines` (L91) | `IntProperty` | `-1` | Add-on Preferences (`preferences.py`:26) | yes | `Int`, default `-1` (L938) |
| `output_file` (L93) | `StringProperty` | `"scene.exr"` | Add-on Preferences (`preferences.py`:16) | yes | `String`, default `"scene.exr"` (L1017) |
| `task_distribution_type` (L95) | `EnumProperty` | `"1"` | Add-on Preferences (`preferences.py`:27) | yes | `Int`, default `Int(1)` (L944) |
| `tmp_dir` (L105) | `StringProperty` | `"/tmp"` | Add-on Preferences (`preferences.py`:17) | yes | `String`, default `""` (L1024) |

**`MoonRayAttributes_Filtering`** -> `scene.moonray.filtering`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `pixel_filter` (L108) | `EnumProperty` | `"1"` | Render props (`ui/mfb_render.py`:135) | yes | `Int`, default `Int(1)` (L598) |
| `pixel_filter_width` (L119) | `FloatProperty` | `3.0` | Render props (`ui/mfb_render.py`:136) | yes | `Float`, default `Float(3.0)` (L592) |
| `texture_blur` (L120) | `FloatProperty` | `0.0` | Render props (`ui/mfb_render.py`:137) | yes | `Float`, default `Float(0.0)` (L586) |

**`MoonRayAttributes_FirefliesRemoval`** -> `scene.moonray.fireflies_removal`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `roughness_clamping_factor` (L123) | `FloatProperty` | `0.0` | Render props (`ui/mfb_render.py`:131) | yes | `Float`, default `Float(0.0)` (L576) |
| `sample_clamping_depth` (L124) | `IntProperty` | `1` | Render props (`ui/mfb_render.py`:132) | yes | `Int`, default `Int(1)` (L569) |
| `sample_clamping_value` (L125) | `FloatProperty` | `10.0` | Render props (`ui/mfb_render.py`:133) | yes | `Float`, default `Float(10.0f)` (L562) |

**`MoonRayAttributes_Frame`** -> `scene.moonray.frame`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `frame` (L129) | `FloatProperty` | `0.0` | **never drawn** | yes | `Float`, default `0.0f` (L189) |
| `max_frame` (L130) | `FloatProperty` | `0.0` | **never drawn** | yes | `Float`, default `0.0f` (L183) |
| `min_frame` (L131) | `FloatProperty` | `0.0` | **never drawn** | yes | `Float`, default `0.0f` (L177) |

**`MoonRayAttributes_GlobalToggles`** -> `scene.moonray.global_toggles`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `cryptomatte_multi_presence` (L134) | `BoolProperty` | `False` | **never drawn** | yes | `Bool`, default `false` (L1145) |
| `enable_displacement` (L136) | `BoolProperty` | `True` | Render props (`ui/mfb_render.py`:44) | yes | `Bool`, default `true` (L862) |
| `enable_dof` (L137) | `BoolProperty` | `True` | Render props (`ui/mfb_render.py`:45) | yes | `Bool`, default `true` (L844) |
| `enable_max_geometry_resolution` (L138) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:46) | yes | `Bool`, default `false` (L849) |
| `enable_motion_blur` (L139) | `BoolProperty` | `True` | Render props (`ui/mfb_render.py`:47) | **no** | `Bool`, default `true` (L840) |
| `enable_presence_shadows` (L140) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:48) | yes | `Bool`, default `false` (L888) |
| `enable_shadowing` (L141) | `BoolProperty` | `True` | Render props (`ui/mfb_render.py`:49) | yes | `Bool`, default `true` (L875) |
| `enable_subsurface_scattering` (L142) | `BoolProperty` | `True` | Render props (`ui/mfb_render.py`:50) | yes | `Bool`, default `true` (L869) |
| `lights_visible_in_camera` (L144) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:51) | yes | `Bool`, default `false` (L896) |
| `max_geometry_resolution` (L145) | `IntProperty` | `2147483647` | Render props (`ui/mfb_render.py`:52) | yes | `Int`, default `Int(INT_MAX)` (L856) |
| `propagate_visibility_bounce_type` (L146) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:53) | yes | `Bool`, default `false` (L903) |
| `shadow_terminator_fix` (L148) | `EnumProperty` | `"0"` | Render props (`ui/mfb_render.py`:54) | yes | `Int`, default `Int(ShadowTerminatorFix::OFF)` (L911) |

**`MoonRayAttributes_ImageSize`** -> `scene.moonray.image_size`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `aperture_window` (L162) | `IntVectorProperty size=4` | `(0, 0, 0, 0)` | **never drawn** | yes | `IntVector`, default `viewportVector` (L240) |
| `image_height` (L165) | `IntProperty` | `1080` | **never drawn** | **no** | `Int`, default `Int(1080)` (L227) |
| `image_width` (L166) | `IntProperty` | `1920` | **never drawn** | **no** | `Int`, default `Int(1920)` (L221) |
| `region_window` (L168) | `IntVectorProperty size=4` | `(0, 0, 0, 0)` | **never drawn** | yes | `IntVector`, default `viewportVector` (L252) |
| `res` (L169) | `FloatProperty` | `1.0` | **never drawn** | yes | `Float`, default `1.0f` (L233) |
| `sub_viewport` (L170) | `IntVectorProperty size=2` | `(0, 0)` | **never drawn** | yes | `IntVector`, default `viewportVector` (L267) |

**`MoonRayAttributes_Logging`** -> `scene.moonray.logging`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `athena_debug` (L173) | `BoolProperty` | `False` | Add-on Preferences (`preferences.py`:35) | yes | `Bool`, default `false` (L1110) |
| `fatal_color` (L174) | `FloatVectorProperty` | `(1, 0, 1)` | Add-on Preferences (`preferences.py`:36) | yes | `Rgb`, default `Rgb(1.0f)` (L1055) |
| `log_debug` (L175) | `BoolProperty` | `False` | Add-on Preferences (`preferences.py`:37) | yes | `Bool`, default `false` (L1045) |
| `log_info` (L176) | `BoolProperty` | `False` | Add-on Preferences (`preferences.py`:38) | yes | `Bool`, default `false` (L1050) |
| `stats_file` (L178) | `StringProperty` | `""` | **never drawn** | yes | `String`, default `""` (L1104) |

**`MoonRayAttributes_MetaData`** -> `scene.moonray.metadata`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `exr_header_attributes` (L181) | `CollectionProperty` | `(none)` | **never drawn** | yes | `SceneObject*`, default `FLAGS_NONE` (L212) |

**`MoonRayAttributes_MotionAndScale`** -> `scene.moonray.motion_and_scale`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `motion_steps` (L184) | `FloatVectorProperty size=2` | `(0, 0)` | **never drawn** | **no** | `FloatVector`, default `defaultMotionSteps` (L278) |
| `scene_scale` (L187) | `FloatProperty` | `0.01` | **never drawn** | yes | `Float`, default `0.01f` (L293) |

**`MoonRayAttributes_PathGuide`** -> `scene.moonray.path_guide`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `path_guide_enable` (L190) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:29) | yes | **ABSENT** - no `path_guide_enable` declared |

**`MoonRayAttributes_ResumeRender`** -> `scene.moonray.resume_render`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `on_resume_script` (L193) | `StringProperty` | `""` | **never drawn** | yes | `String`, default `""` (L830) |
| `resumable_output` (L194) | `BoolProperty` | `False` | **never drawn** | yes | `Bool`, default `false` (L822) |
| `resume_render` (L195) | `BoolProperty` | `False` | **never drawn** | yes | `Bool`, default `false` (L826) |

**`MoonRayAttributes_Sampling`** -> `scene.moonray.sampling`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `bsdf_samples` (L198) | `IntProperty` | `2` | Render props (`ui/mfb_render.py`:73) | yes | `Int`, default `Int(2)` (L367) |
| `bssrdf_samples` (L199) | `IntProperty` | `2` | Render props (`ui/mfb_render.py`:74) | yes | `Int`, default `Int(2)` (L375) |
| `disable_optimized_hair_sampling` (L200) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:75) | yes | `Bool`, default `Bool(false)` (L437) |
| `light_samples` (L201) | `IntProperty` | `2` | Render props (`ui/mfb_render.py`:76) | yes | `Int`, default `Int(2)` (L361) |
| `lock_frame_noise` (L202) | `BoolProperty` | `False` | Render props (`ui/mfb_render.py`:77) | yes | `Bool`, default `false` (L483) |
| `max_depth` (L203) | `IntProperty` | `5` | Render props (`ui/mfb_render.py`:78) | yes | `Int`, default `Int(5)` (L382) |
| `max_diffuse_depth` (L204) | `IntProperty` | `2` | Render props (`ui/mfb_render.py`:79) | yes | `Int`, default `Int(2)` (L389) |
| `max_glossy_depth` (L205) | `IntProperty` | `2` | Render props (`ui/mfb_render.py`:80) | yes | `Int`, default `Int(2)` (L397) |
| `max_hair_depth` (L206) | `IntProperty` | `5` | Render props (`ui/mfb_render.py`:81) | yes | `Int`, default `Int(5)` (L429) |
| `max_mirror_depth` (L207) | `IntProperty` | `3` | **never drawn** | yes | `Int`, default `Int(3)` (L405) |
| `max_presence_depth` (L208) | `IntProperty` | `16` | Render props (`ui/mfb_render.py`:82) | yes | `Int`, default `Int(16)` (L421) |
| `max_subsurface_per_path` (L209) | `IntProperty` | `1` | Render props (`ui/mfb_render.py`:83) | yes | `Int`, default `Int(1)` (L444) |
| `pixel_samples` (L210) | `IntProperty` | `8` | Render props (`ui/mfb_render.py`:84) | yes | `Int`, default `Int(8)` (L354) |
| `presence_threshold` (L211) | `FloatProperty` | `0.999` | Render props (`ui/mfb_render.py`:85) | yes | `Float`, default `Float(0.999)` (L467) |
| `russian_roulette_threshold` (L212) | `FloatProperty` | `0.0375` | Render props (`ui/mfb_render.py`:86) | yes | `Float`, default `Float(0.0375)` (L452) |
| `transparency_threshold` (L213) | `FloatProperty` | `1.0` | Render props (`ui/mfb_render.py`:87) | yes | `Float`, default `Float(1.0)` (L460) |

**`MoonRayAttributes_Volumes`** -> `scene.moonray.volumes`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `max_volume_depth` (L216) | `IntProperty` | `1` | Render props (`ui/mfb_render.py`:105) | yes | `Int`, default `Int(1)` (L413) |
| `volume_attenuation_factor` (L217) | `FloatProperty` | `0.65` | Render props (`ui/mfb_render.py`:106) | yes | `Float`, default `Float(0.65f)` (L535) |
| `volume_contribution_factor` (L218) | `FloatProperty` | `0.65` | Render props (`ui/mfb_render.py`:107) | yes | `Float`, default `Float(0.65f)` (L544) |
| `volume_illumination_samples` (L219) | `IntProperty` | `4` | Render props (`ui/mfb_render.py`:108) | yes | `Int`, default `Int(4)` (L505) |
| `volume_opacity_threshold` (L220) | `FloatProperty` | `0.995` | Render props (`ui/mfb_render.py`:109) | yes | `Float`, default `Float(0.995f)` (L513) |
| `volume_overlap_mode` (L221) | `EnumProperty` | `"0"` | Render props (`ui/mfb_render.py`:110) | yes | `Int`, default `Int(VolumeOverlapMode::SUM)` (L521) |
| `volume_phase_attenuation_factor` (L232) | `FloatProperty` | `0.5` | Render props (`ui/mfb_render.py`:111) | yes | `Float`, default `Float(0.5f)` (L552) |
| `volume_quality` (L233) | `FloatProperty` | `0.5` | Render props (`ui/mfb_render.py`:112) | yes | `Float`, default `Float(0.5f)` (L490) |
| `volume_shadow_quality` (L234) | `FloatProperty` | `1.0` | Render props (`ui/mfb_render.py`:113) | yes | `Float`, default `Float(1.0f)` (L498) |

**`MoonRayAttributes_General`** -> `scene.moonray.general`

| mfb property (`props/attributes.py` line) | mfb type | mfb default | Drawn in UI at | In `get_render_settings()` dict? | Cross-check vs pinned `scene_rdl2` `SceneVariables.cc` |
|---|---|---|---|---|---|
| `batch_tile_order` (L237) | `EnumProperty` | `"4"` | **never drawn** | yes | `Int`, default `Int(4)` (L954) |
| `checkpoint_tile_order` (L254) | `EnumProperty` | `"4"` | **never drawn** | yes | `Int`, default `Int(4)` (L996) |
| `crypto_uv_attribute_name` (L271) | `StringProperty` | `""` | **never drawn** | yes | `String`, default `""` (L661) |
| `fps` (L274) | `FloatProperty` | `24.0` | **never drawn** | yes | `Float`, default `24.0f` (L286) |
| `light_sampling_mode` (L276) | `EnumProperty` | `"0"` | **never drawn** | yes | `Int`, default `Int(0)` (L336) |
| `light_samping_quality` (L286) | `FloatProperty` | `0.5` | **never drawn** | **no** | **ABSENT** - no `light_samping_quality` declared |
| `max_adaptive_samples` (L291) | `IntProperty` | `4096` | **never drawn** | yes | `Int`, default `Int(4096)` (L319) |
| `min_adaptive_samples` (L296) | `IntProperty` | `16` | **never drawn** | yes | `Int`, default `Int(16)` (L311) |
| `progressive_tile_order` (L301) | `EnumProperty` | `"4"` | **never drawn** | yes | `Int`, default `Int(4)` (L975) |
| `sampling_mode` (L318) | `EnumProperty` | `"0"` | **never drawn** | yes | `Int`, default `Int(0)` (L299) |
| `target_adaptive_error` (L328) | `FloatProperty` | `10.0` | **never drawn** | yes | `Float`, default `Float(10.0)` (L328) |
| `two_stage_output` (L333) | `BoolProperty` | `True` | **never drawn** | yes | `Bool`, default `true` (L1036) |

### 1.4 Divergences from pinned `scene_rdl2` — the actionable part

#### (a) Removed / non-existent upstream — mfb exposes settings MoonRay no longer has

| mfb name | Where | Upstream status at pin |
|---|---|---|
| `path_guide_enable` | `props/attributes.py:190`, drawn at `ui/mfb_render.py:29`, sent at `engine/__init__.py:115` | **ABSENT.** No `path_guide*` attribute in `SceneVariables.cc`; a full recursive tree listing of `moonray` @ `eef67ae9` (1 727 paths) contains **no path matching `guid`** — the path-guiding subsystem is not in the pinned tree. |
| `debug_rays_file`, `debug_rays_primary_range`, `debug_rays_depth_range` | `engine/__init__.py:192-198` (dict only; no `PropertyGroup` backs them) | **ABSENT** from `SceneVariables`. |
| `light_samping_quality` | `props/attributes.py:286` | Typo for upstream `light_sampling_quality` (`SceneVariables.cc:344`). Never drawn, so the typo never surfaced. |

`HorrorPills/…` repeats the same stale assumption independently: `addon/properties.py:54` declares
`use_path_guiding` **defaulting to `True`**.

**Phase 06/07 action:** path guiding must not appear in our settings surface or IPC schema.

#### (b) Upstream `SceneVariables` mfb has no property for (12)

`deep_format` (`:612`), `light_sampling_quality` (`:344`, only the typo'd name exists),
`presence_quality` (`:474`), `primary_aov` (`:1031`), `slerp_xforms` (`:282`),
`volume_indirect_samples` (`:881`), and the six `fatal_*` debug probes —
`fatal_bool` (`:1062`), `fatal_int` (`:1069`), `fatal_vec4f` (`:1076`), `fatal_rgba` (`:1083`),
`fatal_mat3f` (`:1090`), `fatal_mat4f` (`:1097`).

Of these only three matter to us near-term: **`slerp_xforms`** (rotation interpolation for motion blur —
Phase 06; comment at `:284`: *"If use_rotation_motion_blur is false this will use slerp to interpolate the
node_xform for motion blur"*), **`presence_quality`** (Phase 07 alpha/presence work) and **`deep_format`**.
The `fatal_*` set is upstream's own shader-error-probe scaffolding, not user-facing settings.

#### (c) Wrong defaults / wrong types — the ones that would produce wrong renders

| Name | mfb | Upstream (pinned) | Why it matters |
|---|---|---|---|
| `aperture_window`, `region_window` | `IntVectorProperty(size=4, default=(0,0,0,0))` (`attributes.py:162,168`) | `IntVector` initialised to `viewportVector = {INT_MIN, INT_MIN, INT_MIN, INT_MIN}` (`SceneVariables.cc:239-240,252`) | `INT_MIN` is the **"unset" sentinel**, not zero. `getSubViewport()` tests `viewportVector[0] == std::numeric_limits<int>::lowest()` to mean unset (`:1437-1444`). Sending `0` is a *valid zero-size window*, not "leave alone". |
| `sub_viewport` | `IntVectorProperty(`**`size=2`**`, default=(0,0))` (`attributes.py:170`) | 4-element `IntVector`, same `INT_MIN` sentinel (`:267`) | Wrong arity **and** wrong sentinel. |
| `debug_pixel` | `IntVectorProperty(size=2, default=(0,0))` (`attributes.py:68`) | 2-element `IntVector` = `{INT_MIN, INT_MIN}`; unset test at `:1424-1429` | Correct arity, wrong sentinel — `(0,0)` means "render only pixel 0,0". |
| `motion_steps` | `FloatVectorProperty(size=2, default=(0,0))` (`attributes.py:184`) | `FloatVector` = `{-1.0f, 0.0f}` (`SceneVariables.cc:277-278`), commented *"Frame-relative time offsets for motion sampling"* | `(0,0)` collapses both motion samples onto the same instant → **motion blur silently disabled**. Direct Phase 06 hazard. |
| `checkpoint_max_snapshot_overhead` | `default=2.0` (`attributes.py:46`) | `Float(0.0f)` (`:801`) | mfb invents a nonzero default. |
| `tmp_dir` | `default="/tmp"` (`attributes.py:105`) | `String("")` (`:1024`) | Hard-codes a POSIX path as a *default*, not a fallback. |
| `deep_id_attribute_names` | `CollectionProperty` of a custom `MoonRayDeepIDAttribute` struct (`attributes.py:84`, `props/deep.py`) | `StringVector` (`:647`) | Over-modelled; upstream wants a flat list of strings. |
| `exr_header_attributes` | `CollectionProperty` of `MoonRayEXRHeaderAttribute` (`attributes.py:181`, `props/meta.py`) | `SceneObject*` with `INTERFACE_METADATA` (`:212`) | Upstream expects a *reference to a `Metadata` scene object*, not inline records. |

The remaining mismatches the diff flagged (`fatal_color`, `max_geometry_resolution`, `shadow_terminator_fix`,
`volume_overlap_mode`, and the `PointerProperty` rows) are representational only — `Rgb(1,0,1)` vs `(1,0,1)`,
`INT_MAX` vs `2147483647`, enum-as-string vs enum-as-int — and are **not** defects.

#### (d) Correctly covered, and worth reusing as a checklist

The sampling (16), volume (9), global-toggle (12), filtering/fireflies (6), checkpoint (14) and
caching (3) groups all match upstream names, types and defaults exactly. That is the genuinely useful part of
mfb: **a validated, near-complete name/default inventory of `SceneVariables` organised into sensible UI groups.**
Re-derive our own from `SceneVariables.cc` (as §1.3 does), but mfb's *grouping* (Caching / Camera and Layer /
Checkpoint / Debug / Deep Images / Driver / Filtering / Fireflies Removal / Frame / Global Toggles / Image Size /
Logging / Metadata / Motion and Scale / Path Guide / Resume Render / Sampling / Volumes / General) is a
reasonable starting taxonomy and tracks upstream's own `setGroup` grouping closely.

#### (e) One real crash bug in the UI, worth remembering as a pattern

`ui/mfb_output.py:35` draws `moonray.checkpoint, "checkpoint_checkpoint_sample_cap"`, but the property is
`checkpoint_sample_cap` (`props/attributes.py:60`). This raises at draw time whenever `checkpoint_active` is on
(`ui/mfb_output.py:25`). Similarly, `preferences.py:6` sets `bl_idname = "moonray_for_blender"`, while the repository
directory (and therefore the Python package as cloned) is `mfb`. `AddonPreferences.bl_idname` must equal the
add-on's registered module name; whether it does here depends entirely on what the release zip's top folder is
called, which is not determinable from the repository. Either way it is an unchecked string coupling.

**Pattern to adopt:** string-keyed `layout.prop()` and string-keyed `bl_idname` have no compile-time check.
Phase 06+ should generate the settings surface from one declarative table so a name can only be wrong in one
place.

#### (f) `execution_mode` is not a `SceneVariable` at all

`props/__init__.py:21-70` declares a four-way `execution_mode` enum (Scalar/Vector/XPU/Auto) drawn into the
render-properties header at `ui/mfb_render.py:151`. It is never read by `get_render_settings()`. It could not be:
execution mode lives on the **render options**, not the scene — `moonray/lib/rendering/rndr/RenderOptions.h:184-186`
exposes `getDesiredExecutionMode()` / `setDesiredExecutionMode(mcrt_common::ExecutionMode)` /
`setDesiredExecutionMode(const std::string&)`, and there is no `exec_mode` attribute in `SceneVariables.cc`.

**Phase 06 action:** our IPC contract must separate *scene* settings (→ `SceneVariables`) from *session* settings
(→ `RenderOptions`, applied bridge-side around `RenderContext` construction). mfb conflated them; the
correctness consequence stayed hidden only because nothing was wired.

The docstrings mfb pasted into that enum (`props/__init__.py:38-44,54-59,61`) are verbatim upstream
feature-gap text — vector mode lacks physically-correct overlapping dielectrics / path guiding / variance buffers
/ volume+deep; XPU additionally lacks round bezier curves, round curves with >2 motion samples and meshes with
>2 motion samples, and falls back silently. Consistent with research 04's upstream GPU/XPU section;
**the >2-motion-samples limit is a Phase 06 motion-blur design constraint** if XPU is ever pursued.

#### (g) Adjacent surface mfb also models (not `SceneVariables`; noted so it is not re-discovered later)

`props/render_output.py` (287 lines) models the `RenderOutput` scene-object attributes (AOV `result`,
`output_type`, `channel_name`/`channel_format`/`channel_suffix_mode`, `math_filter`, `lpe`, `material_aov`,
`visibility_aov`, `primitive_attribute`, `state_variable`, cryptomatte options, `denoise`/`denoiser_input`,
`compression`, `exr_dwa_compression_level`, `file_part`), drawn at `ui/mfb_output.py:20-60` and
`ui/mfb_view_layer.py:31-73`. This is **Phase 09** material.

---

## 2. Principled BSDF → DwaBase: `HorrorPills/material_conversion/converter.py`

309 lines. It is the only genuine graph-traversal code in the entire prior-art corpus — and it is **dead code**:
nothing in `addon/` imports `material_conversion`, and `addon/engine.py:72-93` (`render()`) writes no pixels at
all. It is a design sketch that was never executed against MoonRay.

Below, "DwaBase attribute" means an attribute actually declared for `DwaBaseMaterial` at moonshine
`a3c8667298a2` — present in `dso/material/DwaBase/DwaBaseMaterial.json` or in one of the 18 JSON files it
`include`s (`DwaBaseMaterial.json:6-25`). That closure resolves to **101 distinct attributes**. (The
`lib/material/dwabase/json/` directory holds more than that, but `blend.json`, `hair.json`, `hair_diffuse.json`,
`fabric.json`, `fabric_velvet_common.json` and `toon_diffuse.json` are **not** included by `DwaBaseMaterial` and
belong to its sibling materials.)

### 2.1 Socket → attribute → value, as the converter actually writes it

| Blender socket read | converter line | Key it writes | Value transform | Real `DwaBaseMaterial` attribute? | Verdict |
|---|---|---|---|---|---|
| `Base Color` | `:73-82` | `albedo` + invented `albedo_is_texture` | linked → **absolute file-path string**; else `[r,g,b]` (drops alpha) | `albedo` `Rgb` default `Rgb(1,1,1)` `FLAGS_BINDABLE`, `enable if show_diffuse` (`diffuse.json`) | name OK, **type wrong when linked** (§2.3) |
| `Metallic` | `:85-91` | `metallic` + `metallic_is_texture` | Blender's continuous 0..1 passed straight through | `metallic` `Float` default `0.0f` `FLAGS_BINDABLE`; comment: *"enables/disables metallic model (**binary 0\|1 for plausibility**)"* (`DwaBaseMaterial.json`) | **semantics wrong** — a model switch, not a blend weight. Also never sets `metallic_color`/`metallic_edge_color` (`metallic.json`), so a coloured metal renders white. |
| `Roughness` | `:94-100` | `roughness` + `roughness_is_texture` | passthrough | `roughness` `Float` default `0.5f`, min 0 max 1, `enable if show_specular` (`roughness.json`) | correct |
| `Specular IOR Level` (4.x/5.x) else `Specular` else `inputs[4]` (3.x) | `:103-109` | `specular` | passthrough | `specular` `Float` default `1.0f`, group **Advanced**; comment: *"enables/disables specular reflections (binary 0\|1 for plausibility)"* (`specular.json`) | **wrong target.** Blender's `Specular IOR Level` default `0.5f` is an IOR remap; writing `0.5` into DwaBase `specular` halves specular energy. Correct target is `refractive_index`. |
| `IOR` | `:112-116` | **`ior`** | passthrough, fallback `1.45` | **no `ior` attribute exists.** Real one: `refractive_index` `Float` default `1.5f` (`refractive_index.json`) | **wrong name**, and wrong fallback — Blender 5.2.1 `IOR` default is `1.5f` (`node_shader_bsdf_principled.cc:61-62`) |
| `Transmission Weight` or `Transmission` | `:119-121` | `transmission` | passthrough | `transmission` `Float` default `0.0f` `FLAGS_BINDABLE`, *"binary 0\|1 for plausibility"* (`DwaBaseMaterial.json`) | name OK, same binary-semantics caveat |
| `Emission Color` × `Emission Strength` | `:124-134` | `emission` | premultiplies colour by strength, only if strength > 0 | `emission` `Rgb` default `Rgb(1,1,1)` `FLAGS_BINDABLE`, **`enable if show_emission`**; `show_emission` defaults **`false`** (`emission.json`) | name OK; **`show_emission` never set → emission is a no-op** |
| `Coat Weight` or `Clearcoat` | `:137-139` | `clearcoat` | passthrough | `clearcoat` `Float` default `1.0f` `FLAGS_BINDABLE`, **`enable if show_clearcoat`**; `show_clearcoat` defaults **`false`** (`clearcoat.json`) | name OK; **`show_clearcoat` never set → no-op** |
| `Coat Roughness` or `Clearcoat Roughness` | `:141-143` | `clearcoat_roughness` | passthrough | `clearcoat_roughness` `Float` default `0.1f`, gated by `show_clearcoat` | name OK, same gate problem |
| `Anisotropic` | `:146-148` | `anisotropy` | passthrough | `anisotropy` `Float` default `0.0f`, `enable if show_specular` (`anistropy.json`) | correct; ignores `Anisotropic Rotation` and `Tangent`, which belong on `shading_tangent` `Vec2f` |
| `Normal` → `NORMAL_MAP` node → its `Color` | `:151-154`, `:197-211` | **`normal_map`** + `has_normal_map` | file-path string | **no `normal_map` attribute.** Real: `input_normal` `SceneObject*` `INTERFACE_NORMALMAP` + `input_normal_dial` `Float` `1.0f` (`normal.json`) | **wrong name and wrong type** |
| — (docstring only, `:56`) | | `specular_tint` | | **not a `DwaBaseMaterial` attribute.** `primary_specular_tint`/`secondary_specular_tint` exist only in `hair.json`, which `DwaBaseMaterial` does not include | docstring is wrong |

Non-node materials fall back to a `UsdPreviewSurface` dict built from `material.diffuse_color` (`:213-223`); a
node material with no Principled node falls back to flat 0.8 grey (`:225-235`).

### 2.2 Their Blender 3.x/4.x socket-name handling, specifically

Three distinct strategies, in decreasing quality:

1. **`in` test then positional fallback** — `:103-108`:
   `if 'Specular IOR Level' in principled.inputs:` … `else: principled.inputs.get('Specular', principled.inputs[4])`.
   The `in`-test half is fine. The **positional fallback is wrong on Blender 5.2.1**: declaration order in
   `node_shader_bsdf_principled.cc` is `Base Color`(`:36`), `Metallic`(`:41`), `Roughness`(`:52`), `IOR`(`:61`),
   **`Alpha`(`:70`)**, `Thin Wall`(`:77`), `Normal`(`:83`) … so `inputs[4]` is `Alpha`, and the converter would
   silently read alpha as specular. It is only unreachable today because `'Specular IOR Level'` does exist in
   5.2.1 (`:172-173`).
2. **`or`-chained `.get()`** — `:119`, `:137`, `:141`:
   `principled.inputs.get('Transmission Weight') or principled.inputs.get('Transmission')`.
   Correct in effect for 4.x/5.x vs 3.x, but relies on `bpy_prop_collection.get()` returning `None` and on a
   socket object being truthy. It works, but as an implicit contract, not a stated one.
3. **Single `.get()` with no version handling** — `:112` (`IOR`), `:124-125` (`Emission Color`,
   `Emission Strength`), `:146` (`Anisotropic`). These names happen to be stable across 3.x→5.2, so they work by
   luck, not by design.

There is **no** Blender-version detection anywhere in the repository (no `bpy.app.version` reference). The whole
compatibility story is duck-typing on socket names.

### 2.3 What is broken or naive, and what Phase 07 must do differently for Blender 5.2

**Broken / naive in their code**

- **A texture is not a value.** `:76`, `:87`, `:96`, `:153` write an absolute filesystem path *into the same key*
  that would otherwise hold a scalar/colour, plus a sidecar `*_is_texture` boolean. DwaBase does not work that
  way: those attributes are `FLAGS_BINDABLE`, meaning they take a **binding to another `SceneObject` of the
  `Map` class** (e.g. an `ImageMap`), not an inline path.
- **`_find_principled_bsdf` ignores connectivity** (`:36-45`): returns the first node of type `BSDF_PRINCIPLED`
  in `material.node_tree.nodes`, whether or not it reaches `Material Output`. A muted, orphaned or leftover
  preview node wins over the real one.
- **`_traverse_for_texture` returns the first image found anywhere upstream** (`:174-195`): depth-first over
  *all* inputs of *every* upstream node. A `Roughness` socket driven through a Math node whose other input is
  reachable from the base-colour texture returns the base-colour texture.
- **No `ShaderNodeGroup` handling**, no `Mix Shader`, no `Add Shader`, no reroutes. Group nodes terminate the
  traversal at the group boundary.
- **Reads unevaluated data**: `convert_all_materials(scene)` (`:281-298`) iterates `bpy.data.materials` and
  ignores its own `scene` argument entirely; nothing is depsgraph-evaluated, so drivers/animation on
  `default_value` are read at whatever state the datablock happens to be in.
- **`bpy.path.abspath()` without `library=`** (`:168`, `:185`): resolves relative paths against the current blend
  file, which is wrong for linked libraries. No packed-image handling, no UDIM, no colour-space handling.
- **Enable-flags never set**: `show_emission` and `show_clearcoat` both default `false` and gate the attributes
  the converter writes.
- **`visited` set of `bpy` node structs** (`:177-181`): relies on RNA struct hashing for cycle detection.

**What Phase 07 must do differently, for Blender 5.2.1 specifically**

The 5.2.1 Principled surface (from `node_shader_bsdf_principled.cc` @ `9e2066ae`) is 32 input sockets. Nine are
covered above; the rest are not covered at all, and several have obvious DwaBase homes:

| Blender 5.2.1 socket (line) | default | Plausible `DwaBaseMaterial` target |
|---|---|---|
| `Alpha` (`:70`) | `1.0f` | `presence` `Float` `1.0f` `FLAGS_BINDABLE` (`misc.json`) |
| `Thin Wall` (`:77`) | `false` | `thin_geometry` `Bool` `false` (`misc.json`) |
| `Diffuse Roughness` (`:90`) | `0.0f` | `diffuse_roughness` `Float` `0.0f` — Lambert at 0, Oren-Nayar above (`diffuse.json`) |
| `Subsurface Weight/Radius/Scale/IOR/Anisotropy` (`:112-148`) | `0.0f` / `{1,.2,.1}` / `0.005f` / `1.4f` / `0.0f` | `bssrdf` (enum, default `0`), `scattering_color`, `scattering_radius`, `crease_attenuation` (`subsurface.json`) — all `enable if show_diffuse` |
| `Specular IOR Level` (`:172`) | `0.5f` | **not** `specular`; feeds `refractive_index` via the standard 0.5 ↔ IOR 1.5 remap |
| `Specular Tint` (`:183`, a **Color** in 5.2) | white | `metallic_color` / `metallic_edge_color` (`metallic.json`) on the metallic branch; `DwaBaseMaterial` has no dielectric specular tint |
| `Anisotropic Rotation` (`:201`) + `Tangent` (`:208`) | `0.0f` | `shading_tangent` `Vec2f` `(1,0)` (`anistropy.json`) |
| `Coat IOR` (`:244`), `Coat Tint` (`:253`), `Coat Normal` (`:262`) | `1.5f`, white | `clearcoat_refractive_index`, `clearcoat_attenuation_color` (default `Rgb(0.5,0.5,0.5)`), `independent_clearcoat_normal` + `use_independent_clearcoat_normal` (`clearcoat.json`) |
| `Sheen Weight/Roughness/Tint` (`:267-286`) | `0.0f`, `0.5f`, white | `fuzz`, `fuzz_roughness`, `fuzz_albedo`, gated by `show_fuzz` (`fuzz.json`) |
| `Thin Film Thickness/IOR` (`:313,320`) | `0.0`, `1.33f` | `iridescence*` family (`iridescence.json`) |
| `Emission Strength` (`:300`) | **`0.0`** | fold into `emission` **and** set `show_emission` |

Concrete rules for our mapping layer:

1. Walk **backwards from `Material Output`'s `Surface` input**, not from an arbitrary Principled node.
2. Resolve sockets **by name against `bpy.app.version`**, with an explicit per-version table — never by index,
   never by silent `or`-chain.
3. Treat a linked socket as "**create a `Map` scene object and bind it**", never as "write a path string".
4. Set every `show_*` gate whose group we populate (`show_diffuse`, `show_specular`, `show_emission`,
   `show_clearcoat`, `show_fuzz`, `show_transmission`), and honour `enable if` in our own validation.
5. Respect `metallic` / `transmission` / `specular` being **binary plausibility switches**, not weights: derive
   0/1 from Blender's continuous value with a documented threshold, or refuse and report it.
6. Read from the **depsgraph-evaluated** material, and record unsupported nodes as an explicit diagnostic rather
   than silently falling back to grey.

---

## 3. Geometry, transforms, camera, lights: how they actually did it

### 3.1 The blunt finding

**Neither repository contains any geometry, transform or camera export code.** A grep across every `.py` in both
clones for `evaluated_get`, `to_mesh`, `loop_triangles`, `calc_loop_triangles`, `matrix_world`, `foreach_get`,
`polygons`, `vertices` returns **zero hits**. The only `depsgraph` occurrences are:

- `mfb/engine/__init__.py:229-230` — `def update(self, data, depsgraph): super().update(data, depsgraph)`, a pure
  pass-through to `HydraRenderEngine`;
- `mfb/handlers/__init__.py:38` — a `depsgraph_update_post` handler that only injects a
  `MoonRayShaderNode_Output` node into every material (`:5-33`);
- `horrorpills/addon/engine.py:68-104` — `update()`, `view_update()`, `view_draw()` all literally `pass`;
  `render()` calls `begin_result` / `end_result` with nothing in between (`:80-93`).

So there is **no bpy-API prior art for meshes, triangulation, motion blur, units or axis orientation** to
harvest. Everything Phase 06 needs is new work. What *does* exist is below.

### 3.2 mfb's actual export path: delegate everything to Blender's USD exporter

`operators/io.py:66-102` is the whole of it:

```text
bpy.ops.wm.usd_export(filepath=<scene>.usd,
                      selected_objects_only=..., visible_objects_only=...,
                      export_animation=..., export_materials=False)        # io.py:76-81
    |
    v
source ~/.mfb/installs/openmoonray/scripts/setup.sh &&
  ~/.mfb/installs/openmoonray/bin/hd_usd2rdl -in <usd> -out <rdla|rdlb>    # io.py:112-117
    |
    v
for each image in <outdir>/textures: maketx <file>                        # io.py:119-132
```

Everything about geometry, transforms, cameras, motion blur, units and axis orientation is therefore
**Blender's `wm.usd_export` behaviour plus `hd_usd2rdl`'s USD→RDL2 conversion** — neither of which is on this
project's path (ADR-0002). Nothing here transfers.

Visible mistakes in even this thin layer, worth naming:

- **`export_materials=False` is hard-coded** (`io.py:80`) while the operator advertises an `export_materials`
  flag to the user (`io.py:36-40`) — the user's choice is discarded.
- **`subprocess.run(maketx_command, shell=True, ...)` with a *list* argument** (`io.py:130-132`). On POSIX with
  `shell=True`, `subprocess` passes only `args[0]` to the shell and the remainder as `sh` positional parameters
  — so `maketx` runs with **no input file**. The texture-conversion loop cannot have worked.
- `io.py:122` iterates `os.listdir(texture_path)` **unconditionally**; if `hd_usd2rdl` produced no `textures/`
  directory this raises `FileNotFoundError`, which the surrounding `except subprocess.CalledProcessError`
  (`io.py:135`) does not catch.
- The `.rdla`/`.rdlb` choice is derived from the filename extension (`io.py:73-74`); any other extension yields
  `extension = ""` (`io.py:106`) and the conversion silently overwrites the intermediate `.usd`.
- `export_hair`, `export_lights`, `export_cameras` are declared (`io.py:42-58`) and never passed to anything.

### 3.3 Lights: the only substantive light-side content in either repo

`mfb/properties.py:65-86` — `MoonRayLightProperties` on `bpy.types.Light`:
`visible`, `motion_blur`, `texture` (`FILE_PATH`), `lightfilter_set`, `light_set_input`, `shadow_set_input`, and
a `type` enum of `CYLINDER / DISK / DISTANT / ENV / RECT / SPHERE / SPOT` (`:70-82`), drawn at
`ui/mfb_light.py:22` alongside Blender's own `light.color` and `light.energy` (`:29,31`).

Cross-checked against `moonray` @ `eef67ae9`, `dso/light/` contains:
`CylinderLight, DiskLight, DistantLight, EnvLight, MeshLight, PortalLight, RectLight, SphereLight, SpotLight`.
mfb's enum is therefore **correct but incomplete — it omits `MeshLight` and `PortalLight`**, both present at our
pin. `MeshLight` is the natural target for Blender's emissive-material-as-light idiom.

`dso/lightfilter/` contains eight filters (`BarnDoor, ColorRamp, Combine, Cookie, Decay, Intensity, Rod, Vdb`);
mfb models light-filter *sets* (`props/sets.py`, `ui/mfb_light.py:37`) but no filter parameters.

Note the design decision embedded in mfb: it **replaces** Blender's light UI rather than mapping it —
`ui/__init__.py:16-19` excludes `DATA_PT_light`, `DATA_PT_spot`, `NODE_DATA_PT_light` and `DATA_PT_falloff_curve`
and substitutes a MoonRay-native light-type enum, ignoring Blender's own `light.type`
(`POINT/SUN/SPOT/AREA`). That is a legitimate but heavy UX choice: a scene authored that way is not portable back
to Cycles/EEVEE. Phase 06 should decide this deliberately rather than inherit it.

### 3.4 Object-level render attributes

`mfb/properties.py:88-97` (`MoonRayObjectProperties` on `bpy.types.Object`) covers only `is_light`, four
set-membership strings, and a `user_data` collection. `engine/__init__.py:209-221` explicitly gives up on the
rest, in a comment: *"There's also these controls for the objects, but im not so sure how to transfer that data
over"* — listing `moonray:visible_in_camera`, `visible_shadow`, `visible_diffuse_reflection`,
`visible_diffuse_transmission`, `visible_glossy_reflection`, `visible_glossy_transmission`,
`visible_mirror_reflection`, `visible_mirror_transmission`, `visible_volume`, `side_type`.

All ten exist on the RDL2 `Geometry` base class at our pin — `Geometry.cc:74` (`side_type`, default `TWO_SIDED`)
and `:89-151` (the nine `visible_*` booleans, all default `true`). For the Direct Bridge these are trivially
settable per geometry object; it was the Hydra indirection that made them awkward. Small but real win for
architecture A.

`mfb/props/userdata.py` + `operators/userdata.py` also model arbitrary RDL2 user data with typed values
(`BOOL/COLOR/FLOAT/INTEGER/MAT4F/STRING/VEC2F/VEC3F`, drawn at `ui/mfb_object.py:50-70`) — a reasonable shape for
per-object primitive attributes in Phase 06/07, though again never consumed by anything.

### 3.5 `HorrorPills`: environment wiring only

The only non-placeholder content is environment setup: `RDL2_DSO_PATH` = `<root>/rdl2dso`, `MOONRAY_CLASS_PATH` =
`<root>/shader_json`, plus an `LD_LIBRARY_PATH` prepend (`addon/engine.py:42-53`, duplicated in
`addon/utils.py:152-175`). mfb sets the same two plus `ARRAS_SESSION_PATH` and a **two-entry** `RDL2_DSO_PATH`
(`rdl2dso.proxy:rdl2dso`, `engine/__init__.py:22-24`) — the `.proxy` entry is what HorrorPills misses and is what
makes proxy shader-class discovery work.

Two Blender-API defects there that are instructive:

- `addon/engine.py:27-30` overrides `RenderEngine.__init__` and calls `_setup_environment()` from it, which does
  `bpy.context.preferences.addons[__package__.split('.')[0]].preferences` (`:34`) — a `KeyError` the moment the
  package name and the registered add-on key disagree, raised during engine instantiation, i.e. at render time.
- `addon/engine.py:110` `from bl_hydra import HydraRenderEngine` — `bl_hydra` is not a Blender module (the real
  API is `bpy.types.HydraRenderEngine`, which mfb uses correctly at `mfb/engine/__init__.py:3`). The `try` at
  `:109` therefore always fails, `HYDRA_AVAILABLE` is always `False` (`:154`), and only the pixel-less
  placeholder engine registers (`:160`). Research 04 called this; it is confirmed at source.

---

## 4. Blender/MoonRay pitfalls found in the code that Phases 06–08 will hit

Ordered by how likely they are to bite us. "Applicability" is judged against **our** path:
custom binding → `scene_rdl2` → `RenderContext`, no Hydra, no USD.

| # | Pitfall | Evidence | Applicability to Direct Bridge |
|---|---|---|---|
| 1 | **`INT_MIN` is the "unset" sentinel for windowing SceneVariables**, not `0`. | `SceneVariables.cc:239-240,252,267,1119-1120`; unset tests at `:1424-1429,1437-1444`. mfb got this wrong at `props/attributes.py:68,162,168,170`. | **High — Phase 06/08.** Border render and viewport sub-viewport both go through `sub_viewport`/`region_window`. Our IPC schema needs an explicit *absent* encoding that the bridge maps to `INT_MIN`, not a defaulted `0`. |
| 2 | **`motion_steps` default is `{-1.0, 0.0}`, not `{0,0}`.** | `SceneVariables.cc:277-278`; mfb `props/attributes.py:184`. | **High — Phase 06.** Writing `(0,0)` disables motion blur while looking configured. Pair with `Camera.mb_shutter_open = -0.25f` / `mb_shutter_close = 0.25f` (`Camera.cc:52,56`) and Blender's `scene.render.motion_blur_shutter`. |
| 3 | **`RdlMeshGeometry.is_subd` defaults to `true`.** | `dso/geometry/RdlMesh/attributes.cc:153-158`: *"If true, a SubdivisionMesh primitive will be created - PolygonMesh otherwise"*. | **High — Phase 06.** A depsgraph-evaluated Blender mesh is a polygon mesh. Forgetting `is_subd = false` turns every mesh into a subdivision surface and geometry silently diverges from the viewport. Neither prior repo hit this because neither ever wrote a mesh. |
| 4 | **DwaBase `show_*` gates default off for emission and clearcoat.** | `emission.json` `show_emission` default `false`; `clearcoat.json` `show_clearcoat` default `false`. HorrorPills sets `emission`/`clearcoat` without them (`converter.py:130,139`). | **High — Phase 07.** Identical for us; RDL2 attribute writes carry the same gating. |
| 5 | **`FLAGS_BINDABLE` means "bind a `Map` object", not "assign a path".** | `diffuse.json`, `roughness.json`, `metallic.json` etc. all carry `"flags": "FLAGS_BINDABLE"`; `converter.py:76,87,96,153` assigns path strings. | **High — Phase 07.** Our translation layer must create `Map`-class scene objects and use RDL2 attribute *bindings*. This shapes the material message format. |
| 6 | **Camera film/lens defaults and conventions differ from Blender's.** | `dso/camera/PerspectiveCamera/attributes.cc:38` `focal` default `30.0f`; `:62` `film_width_aperture` default **`24.0f`** (Blender's default `sensor_width` is 36 mm); `:66-68` `pixel_aspect_ratio` is *"ratio of pixel size **y / x**"* (Blender's `pixel_aspect_x`/`pixel_aspect_y` is the inverse); `:72` `dof_aperture` is an aperture **width**, while Blender exposes f-stop. | **High — Phase 06.** Each of these is a silent framing/DoF error if copied naively. No prior repo ever mapped a camera. |
| 7 | **Execution mode is a `RenderOptions` concern, not a `SceneVariable`.** | `RenderOptions.h:184-186`; no `exec_mode` in `SceneVariables.cc`. mfb wired an enum to nothing (`ui/mfb_render.py:151`). | **High — Phase 06 IPC contract.** Split scene vs. session settings in the message schema now, not later. |
| 8 | **Path guiding is gone from the pinned tree.** | No `path_guide*` in `SceneVariables.cc`; no `guid`-matching path in moonray's 1 727-entry tree at `eef67ae9`. Both prior repos still expose it (`mfb props/attributes.py:190`; `HorrorPills addon/properties.py:54`, default `True`). | **Medium.** Cheap to avoid, embarrassing to ship. |
| 9 | **`Geometry.side_type` defaults to `TWO_SIDED` and all nine `visible_*` default `true`.** | `Geometry.cc:74,89-151`. | **Medium — Phase 06/07.** Blender's per-object ray-visibility flags map near one-to-one; mfb explicitly punted (`engine/__init__.py:210`). Easy win for us. |
| 10 | **`node_xform` is `Mat4d` (double).** | `Node.cc:34`. | **Medium — Phase 06.** `addon/scene_writer.py:154-176` currently emits float literals into RDL2 ASCII, which RDL2 coerces; once the bridge sets attributes natively via `AttributeKey<Mat4d>`, precision and row layout must match. |
| 11 | **A `GeometrySet` may be required for a valid render even when nothing references it.** | Recorded as *reported, not source-verified* in [`docs/bridge/SCENE_TRANSLATION.md`](../bridge/SCENE_TRANSLATION.md) (OpenMoonRay discussion #223). **Not resolved by this harvest** — no prior repo ever built a `SceneContext`. | **High — Phase 06 blocker risk.** Confirm against `GeometrySet.h/.cc` + `RenderContext` early; it gates the whole geometry path. |
| 12 | **Instancing has two mutually exclusive input methods.** | `dso/geometry/RdlInstancerGeometry/attributes.cc:32-35` `method` enum: `0 = "xform attributes"` (then `positions` / `orientations` as **Vec4f quaternions** / `scales` / `velocities`, `:68-98`) or `2 = "xform list"` (then `xform_list` as `Mat4dVector`, `:59-65`); `ref_indices` selects which reference geometry per instance (`:100-105`); `instance_level` supports 5 nesting levels (`:45-51`). | **High — Phase 07.** Blender's `depsgraph.object_instances` yields full 4×4 matrices, so `method = 2` is the natural target; `method = 0` is the memory-efficient path if we decompose. Decide deliberately. No prior art. |
| 13 | **String-keyed UI/property names have no compile-time check.** | `ui/mfb_output.py:35` (`checkpoint_checkpoint_sample_cap` vs the real `checkpoint_sample_cap`), `props/attributes.py:286` (`light_samping_quality`), `preferences.py:6` (`bl_idname` string vs the installed module name). | **Medium — all phases.** Argues for generating our settings surface from one table. |
| 14 | **`subprocess.run(list, shell=True)` silently drops arguments on POSIX.** | `mfb operators/io.py:130-132`. | **Low but real — Phase 07 texture pipeline.** If we shell out to `maketx`/`oiiotool` for `.tx` conversion, pass a list **without** `shell=True`. |
| 15 | **Blender socket lookup by index is version-fragile.** | `converter.py:108` `principled.inputs[4]`; in Blender 5.2.1 index 4 is `Alpha` (`node_shader_bsdf_principled.cc:70`). | **High — Phase 07.** Name-based lookup keyed on `bpy.app.version` only. |
| 16 | **XPU caps motion samples at 2 for meshes and round curves.** | Verbatim upstream text quoted at `mfb props/__init__.py:56-59`; consistent with research 04. | **Low now, Medium if XPU is revisited.** Constrains any multi-sample motion-blur design. |
| 17 | **A Windows-native MoonRay build was attempted twice and abandoned.** | mfb history: `5c21a2ba` "almost successfull windows build" (2024-11-11; adds `building/windows_build.bat`, `building/windows_x64/` cmake configs, a vendored `libmicrohttpd.lib`), `10659d9a` "removed windows setup" (2025-04-09), `c5d8e530` "add windows (broken)" (2025-04-10), `0262e530` "windows build (not recognizing blender deps)" (2025-04-10), then `da737bb5` "revert to addon" (2025-05-17). | **Informational.** Independent corroboration for the WSL2-host decision; changes nothing. |

### 4.1 Phase 08 specifically

The prior-art corpus contains **nothing** for the interactive viewport: `view_update`/`view_draw` are `pass` in
HorrorPills (`addon/engine.py:95-104`), and mfb has no override at all — it inherits Hydra's loop. No progressive
loop, no cancellation, no restart-on-scene-change, no frame transport, no resolution scaling. Research 04 said
this; this harvest confirms it at source.

The only Phase-08-relevant facts recovered are upstream ones, and they are worth knowing before designing:
`progressive_tile_order` (`SceneVariables.cc:975-995`, morton default), **`fast_geometry_update`**
(`:676-683` — keeps tessellation data resident so geometry can be re-tessellated after updates instead of being
rebuilt; directly relevant to a viewport edit loop, and mfb buried it in Add-on Preferences at
`preferences.py:30`), and `checkpoint_snapshot_interval` / `checkpoint_bg_write` (`:812,759`) as an existing
snapshot mechanism worth understanding before inventing our own.

---

## 5. What NOT to take

Everything here is Hydra-, USD- or `hd_usd2rdl`-bound, or is a mistake, and must not enter our codebase or our
design vocabulary.

1. **`bpy.types.HydraRenderEngine` + `bl_delegate_id`** (`mfb/engine/__init__.py:3,12`). ADR-0002 rejects the
   Hydra path and upstream confirms it does not render in Blender. Our engine is `bpy.types.RenderEngine`
   (`addon/engine.py:22`) and stays that way.
2. **`get_render_settings(self, engine_type)`** (`mfb/engine/__init__.py:40`) and its
   `"sceneVariable:"` / `"sceneVariable_"` **dual-prefix key scheme** (`:58-59,62-63,65-66,68-69,133-134,
   184-185,189-190,194-195,197-198`). That duplication exists to satisfy Hydra render-settings namespacing.
   Our IPC schema must use plain attribute names; do not import the prefixes or the duplication.
3. **The `hd_usd2rdl` pipeline** (`mfb/operators/io.py:104-137`) and `bpy.ops.wm.usd_export` (`:76`). We never go
   through USD; drop the `keep_usd` / intermediate-`.usd` concept entirely.
4. **`pxr.Plug.Registry().RegisterPlugins()` and `PXR_PLUGINPATH_NAME` wiring**
   (`mfb/engine/__init__.py:16,29,37`). There is no USD plugin registry in our path.
5. **`build.py`'s NDR-header workaround** (`mfb/build.py:433+`, the `NDR_HEADERS` dict). It fabricates
   `pxr/usd/ndr/api.h` and `declare.h` **as verbatim Pixar-copyrighted source embedded in Python string
   literals** (`build.py:436,469,522,598,664,727` all carry `// Copyright 2018 Pixar`). It exists only because
   hdMoonray needs NDR headers that newer USD removed. We do not build hdMoonray, and copying it would drag
   Pixar-licensed text into our tree (§6).
6. **`build.py`'s `pxrConfig.cmake` shim that points every USD target at Blender's `libusd_ms.so`**
   (`mfb/build.py:113-192`). Linking MoonRay against Blender's monolithic USD build is exactly the fragility our
   out-of-process bridge exists to avoid.
7. **`HorrorPills`' `bl_hydra` import** (`addon/engine.py:110,126,133`) and the whole `MoonRayHydraEngine` class.
   The module does not exist; the class is unreachable.
8. **`HorrorPills`' `export_to_usd_material()`** (`converter.py:237-278`). It builds a nested dict labelled
   `'id': 'moonray:DwaBase'` and calls it USD. It touches no `pxr` API and produces nothing consumable.
9. **`*_is_texture` / `has_normal_map` sidecar booleans** (`converter.py:77,88,100,154`) — an artefact of
   encoding textures as path strings. Our schema encodes a bound `Map` object reference, which is
   self-describing.
10. **mfb's ~100 empty shader-node classes** (`nodes/shaders/mfb_shader_nodes_shader.py`, 30 classes;
    `mfb_shader_nodes_map.py`, 65 classes; `mfb_shader_nodes_normal.py`; `..._displacement.py`;
    `mfb_lightshader_nodes_lightfilter.py`; `nodes/comp/mfb_comp_nodes_displayfilter.py`). Every `init()` and
    `update()` body is `pass` (e.g. `mfb_shader_nodes_shader.py:8-12`, and identically for every class after
    it). They subclass `bpy.types.ShaderNode` directly (`nodes/mfb_nodes.py:3`) with no sockets and no `poll`.
    The **class-name inventory** is mildly useful as a list of MoonRay shader DSOs; the code is not.
11. **The `depsgraph_update_post` handler that mutates every material** (`mfb/handlers/__init__.py:5-38`).
    Injecting nodes into user data from a depsgraph callback on every update is both a data-integrity and a
    performance hazard.
12. **`path_guide_enable` / `use_path_guiding`** — see §4 #8.
13. **`HorrorPills`' `README.md` / `PROJECT_OVERVIEW.md` "implemented" claims.** Research 04 established the
    doc/code mismatch; treat both files as having zero evidentiary value.

---

## 6. Licensing verdicts, fragment by fragment

Our repository is **GPL-3.0-or-later** (`LICENSE`, `NOTICE.md`).

### 6.1 `cjhosken/mfb` — GPL-3.0 (re-verified live, 2026-09-10)

`gh api repos/cjhosken/mfb` returns `license.spdx_id = "GPL-3.0"`; `LICENSE.txt` in the clone is the verbatim
620-line GPLv3 text. **Compatible** with GPL-3.0-or-later.

Two attribution complications, both verified in the clone:

- **No per-file copyright headers.** `props/attributes.py:1`, `engine/__init__.py:1` and `operators/io.py:1` all
  begin directly with `import bpy`; a repo-wide grep for `Copyright`/`SPDX` in `*.py` matches **only** the
  embedded Pixar headers inside `build.py`. `LICENSE.txt` itself carries no filled-in copyright line. The only
  authorship statement anywhere is `__init__.py:5` — `"author": "Christopher Hosken"`. Attribution must
  therefore be constructed by us (author name + repo URL + commit SHA), not copied.
- **`README.md:30-34` declares mfb itself derives from `RenderManForBlender` and `BlendLuxCore`.** We have not
  verified that chain, and it does not matter for reference-only use — but it **would** matter before any literal
  copy, because mfb cannot relicense code it took from elsewhere.

| Fragment we might want | Location | License | Verdict |
|---|---|---|---|
| `SceneVariables` name/type/default/grouping inventory | `props/attributes.py` (362 lines) | GPL-3.0 | **Reference-only, and re-derive.** §1.4 documents 10 concrete errors in it; §1.3 already re-derives the correct table from `SceneVariables.cc`. Copying it would import its bugs and create an attribution obligation for no benefit. |
| Upstream enum-meaning comments (exec modes, tile orders, pixel filters) | `props/__init__.py:25-67`, `engine/__init__.py:73-176`, descriptions throughout `props/attributes.py` | GPL-3.0 *on the file*, but the text is transcribed from OpenMoonRay docs (CC-BY-4.0 upstream) | **Reference-only.** If we want this text, take it from `docs/vendor/openmoonray/` under its own CC-BY-4.0 (already vendored, with `ATTRIBUTION.md`), not laundered through mfb. |
| Cycles-style panel include/exclude pattern | `ui/__init__.py:13-45` (`get_panels()`, `COMPAT_ENGINES`) | GPL-3.0 | **Reuse permitted with attribution**, but it is ~30 lines of a widely replicated Blender idiom (mfb's own comment at `:14` says "Follow the Cycles model"). **Reference-only recommended** — write our own from the Blender manual. |
| Light-type enum + light property surface | `properties.py:65-86`, `ui/mfb_light.py` | GPL-3.0 | **Reference-only.** Incomplete (no `MeshLight`/`PortalLight`) and re-derivable from `dso/light/` in one command. |
| `build.py` NDR-header workaround | `build.py:433+` | GPL-3.0 wrapper containing **Pixar-copyrighted USD headers** (`// Copyright 2018 Pixar`, "Licensed under the terms set forth in the LICENSE.txt file available at https://openusd.org/license") | **Do not reuse.** Also unnecessary (§5 #5). Embedding third-party licensed source inside a GPL file does not relicense it. |
| `build.py` USD / `pxrConfig` shim | `build.py:113-192` | GPL-3.0 | **Do not reuse** (§5 #6). |
| Anything Hydra/USD | `engine/__init__.py`, `operators/io.py` | GPL-3.0 | **Do not reuse** (§5 #1–#4). |

**Practical rule for Phase 06/07:** if we ever do copy a literal fragment from `cjhosken/mfb`, add an entry to
`NOTICE.md` naming the file, the upstream repo URL, commit `b0b17cfe56e84cde62363d7ad44b5bc60ec91b0b`, the author
(Christopher Hosken) and GPL-3.0, and keep the fragment identifiable. Nothing in this harvest recommends doing
so.

### 6.2 `HorrorPills/MoonRay-Blender-Integration` — no license (re-verified live, 2026-09-10)

`gh api repos/HorrorPills/MoonRay-Blender-Integration` returns **`"license": null`**. The contents API for the
repository root lists exactly `PROJECT_OVERVIEW.md, README.md, addon, build_scripts, docs, material_conversion,
tests` — **no LICENSE file**, seven months after the repository was created. `README.md:26` ("Free & Open:
Apache 2.0 licensed") and `README.md:276` ("This project code: Apache 2.0 License") are unsupported assertions,
and GitHub's own detector agrees they are unsupported. Nothing has changed since research 04.

**Verdict: all-rights-reserved. Design reference only. No literal code, comments or docstrings may be
transferred — including from `material_conversion/converter.py`.**

What §2 extracts from it is *facts about the mapping problem* — which Blender socket names changed between 3.x
and 4.x/5.x, which DwaBase attribute names are wrong, which gates are left unset — restated in our own words and
cross-checked against upstream source we can read under its own license (`moonshine`, Apache-2.0; `blender`,
GPL-2.0-or-later). That is unencumbered. The 309-line file itself is not, and Phase 07 must be written from the
DwaBase JSON schemas and the Blender node source, **not** from that file open on screen.

If a LICENSE file ever appears there, this verdict can be revisited — but given the defect list in §2.3, there is
little worth the paperwork.

### 6.3 Upstream sources used for cross-checking

`scene_rdl2`, `moonray` and `moonshine` are Apache-2.0; `blender` is GPL-2.0-or-later; the vendored OpenMoonRay
documentation under `docs/vendor/openmoonray/` is CC-BY-4.0 with attribution recorded in
`docs/vendor/openmoonray/ATTRIBUTION.md`. Facts read out of these (attribute names, types, defaults) are not
themselves copyrightable; any literal code taken from them would need the usual Apache-2.0 / GPL handling and a
`NOTICE.md` entry.

---

## 7. Actionable: what feeds straight into Phase 06 and Phase 07

Nothing below activates a phase. These are ready inputs for when Phase 06 is approved.

### Phase 06 — geometry, transforms, camera, lights

**Ready-to-use inputs**

1. **Camera mapping table** (from `dso/camera/PerspectiveCamera/attributes.cc` + `scene_rdl2/Camera.cc`), with
   four unit/convention traps already identified: `focal` ← `camera.lens` (mm; MoonRay default 30 vs Blender 50);
   `film_width_aperture` ← `camera.sensor_width` (**MoonRay default 24, Blender default 36**);
   `pixel_aspect_ratio` = **y/x** (invert Blender's); `dof` / `dof_aperture` / `dof_focus_distance` ←
   `use_dof` / f-stop→aperture-width conversion / `focus_distance`; `horizontal_film_offset` /
   `vertical_film_offset` ← `shift_x` / `shift_y`; `near` / `far` ← `clip_start` / `clip_end`
   (`Camera.cc:47,49`, defaults 1.0 / 10000.0); `mb_shutter_open` / `mb_shutter_close` / `mb_shutter_bias`
   (`Camera.cc:52,56,60`, defaults −0.25 / 0.25 / 0.0) ← `scene.render.motion_blur_shutter`.
2. **Mesh attribute contract** (from `dso/geometry/RdlMesh/attributes.cc`): `face_vertex_count` (IntVector),
   `vertices_by_index` (IntVector), `vertex_list_0` / `vertex_list_1` (Vec3fVector; `_1` is the second motion
   step, `:70-75`), `velocity_list_0/1`, `acceleration_list`, `uv_list` (Vec2fVector, **per face-vertex**,
   `:132-137`), `normal_list` (Vec3fVector, **per face-vertex**, `:139-144`), `orientation`
   (`right-handed` default, `:99-108`), `part_list` / `part_face_count_list` / `part_face_indices`
   (multi-material partitioning, `:110-131`), `velocity_scale` (`:146-151`), **`is_subd` — must be explicitly
   set `false`** (`:153-158`), the five `subd_*` attributes, and `primitive_attributes` (SceneObjectVector).
   Upstream also ships `dso/geometry/RdlMesh/polymesh2rdlmesh.py` (Apache-2.0) as a reference exporter — read it
   before writing ours.
3. **Per-object visibility contract**: the ten `Geometry` attributes at `Geometry.cc:74,89-151` (`side_type`
   default `TWO_SIDED` plus nine `visible_*` defaulting `true`), mapping near one-to-one onto Blender's object
   ray-visibility flags. mfb explicitly abandoned these (`engine/__init__.py:210`); we get them almost free.
4. **Light class list at our pin**: `Cylinder, Disk, Distant, Env, Mesh, Portal, Rect, Sphere, Spot` — note
   `MeshLight` and `PortalLight`, which mfb's enum omits. Phase 05 already found and worked around a real
   SphereLight / non-axis-aligned DistantLight anomaly in this build
   (`docs/completions/05-blender-renderengine-integration.md`); Phase 06 should root-cause it against
   `moonray/lib/rendering/pbr/light/` before extending the light set.
5. **Corrected `SceneVariables` checklist** — §1.3 plus the §1.4(b) gap list, replacing mfb's coverage table.
6. **IPC schema split** to design explicitly (§4 #7): *scene* attributes → `SceneVariables`; *session* attributes
   (execution mode, thread count, machine id) → `RenderOptions`, applied bridge-side.
7. **Sentinel encoding decision** (§4 #1): the wire format needs a distinct "unset" for `aperture_window` /
   `region_window` / `sub_viewport` / `debug_pixel`, mapped to `INT_MIN` on the bridge side.
8. **Open blocker to resolve first**: whether a `GeometrySet` must exist for a valid render (§4 #11) —
   unverified, no prior art, and it gates the entire geometry path.

**Explicitly not available from prior art:** mesh extraction, triangulation, depsgraph evaluation, motion-blur
sampling, axis conversion, unit handling, update/delete semantics. Phase 06's tasks "Create canonical translation
schema", "Validate coordinate systems/unit conventions" and "Validate edit/update/delete" have **zero** prior art.
Our own `addon/scene_writer.py:97,133-176` (Blender Z-up → RDL2 Y-up as `(x, z, −y)`, plus the `Mat4` row layout
established in Phase 05) remains the only implemented reference, and it is baseline-scope, not general.

### Phase 07 — materials, textures, instances

**Ready-to-use inputs**

1. **The `DwaBaseMaterial` attribute schema itself** — `dso/material/DwaBase/DwaBaseMaterial.json` plus its 18
   includes: 184 declarations, each with type, default, `flags`, `group` and `enable if`. This is the
   authoritative target and it is machine-readable, so Phase 07's "Define explicit support matrix" task can be
   generated from it directly. `moonray` core also ships `dso/material/UsdPreviewSurface` as a lower-dependency
   alternative target (already noted in `UPSTREAM_LOCK.json`'s `moonshine` entry).
2. **The Blender 5.2.1 Principled socket list** — 32 sockets with names, types, panel grouping and defaults,
   extracted from `node_shader_bsdf_principled.cc` @ `9e2066ae` (§2.3 table). That is the left-hand column of the
   mapping.
3. **A corrected socket→attribute draft** (§2.1 + §2.3): the nine mappings HorrorPills attempted with their three
   name errors fixed (`ior` → `refractive_index`; `normal_map` → `input_normal` + `input_normal_dial`;
   `specular` ← an IOR remap of `Specular IOR Level` rather than a passthrough), plus the twelve uncovered socket
   groups with plausible targets.
4. **The six `show_*` gates** that must be set alongside their groups (§2.3 rule 4).
5. **Binding model**: `FLAGS_BINDABLE` attributes take a bound `Map` scene object; the texture path belongs on
   the `Map`, not on the material (§4 #5). This determines the shape of our material message.
6. **Instancing contract** — `dso/geometry/RdlInstancerGeometry/attributes.cc`: choose `method = 2` +
   `xform_list` (`Mat4dVector`) to consume `depsgraph.object_instances` matrices directly, or `method = 0` +
   `positions` / `orientations` (Vec4f quaternions) / `scales` / `velocities` for the compact path;
   `references` + `ref_indices` select per-instance source geometry; `instance_level` supports 5 nesting levels.
   No prior art at all — decide with the memory benchmark Phase 07's task list already requires.
7. **Traversal rules** (§2.3): start from `Material Output.Surface`, name-based lookup keyed on
   `bpy.app.version`, depsgraph-evaluated data, and explicit unsupported-node diagnostics rather than a silent
   grey fallback.

**Explicitly not available from prior art:** any working Principled→DwaBase conversion, any texture `.tx` /
colour-space handling (mfb's `maketx` loop is broken, §3.2), UV-set selection, multi-material assignment via
`part_list`, or instancing of any kind.

---

## 8. Summary judgement

- `cjhosken/mfb` contributes **one thing of real value**: a near-complete, sensibly grouped enumeration of
  `SceneVariables` — which this document has now re-derived correctly and corrected in ten places, so the
  original is no longer needed.
- `HorrorPills/…` contributes **one thing of real value**: an inventory of the Blender-version socket-name
  problem — which this document has now restated in our own words against Blender 5.2.1 source, so the original
  is no longer needed (and, being unlicensed, could not have been used anyway).
- Everything else the prior-art corpus would need to offer for Phases 06–08 — geometry, transforms, cameras,
  motion blur, units, axes, instancing, viewport, cancellation, crash recovery — **does not exist**, in any of
  the repositories, in any form. Research 04 established this about outcomes; this harvest confirms it at the
  level of individual `bpy` API calls.
- The most valuable output of this harvest is therefore not borrowed code but the **17-item pitfall list in §4**
  and the upstream-verified contracts in §7 — none of which either prior project ever got far enough to
  discover.
