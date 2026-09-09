# OpenMoonRay Developer Reference (Vendored)

## What this directory is

A pinned, local, versioned copy of the official OpenMoonRay
**developer-reference** documentation, imported from the upstream
[`OpenMoonRay/openmoonray-docs`](https://github.com/OpenMoonRay/openmoonray-docs)
repository, used as an offline implementation reference by contributors and
by Claude Code / Codex agents working on this repository.

Everything under this directory (`docs/vendor/openmoonray/`) is isolated
vendored third-party content. It is licensed CC BY 4.0 upstream — see
[ATTRIBUTION.md](ATTRIBUTION.md) — and is kept separate from this project's
own documentation under `docs/project/`, `docs/decisions/`, `docs/phases/`,
etc. Do not mix our own project documentation into this tree, and do not
edit the vendored content by hand — refresh it with
`scripts/sync_openmoonray_docs.py` instead.

## Source of truth

The upstream OpenMoonRay repositories and the live documentation site
(<https://docs.openmoonray.org/>) remain authoritative. This directory is a
**snapshot**, pinned to the exact commit recorded in
[UPSTREAM.json](UPSTREAM.json), and can go stale. When in doubt, or when the
local copy might be out of date, check the live site or the upstream repo.

## How agents should use it

For MoonRay-specific implementation questions — before assuming behavior —
inspect the relevant local file(s) under
`docs/vendor/openmoonray/developer-reference/` first. This is especially
relevant when working with:

- `moonray::rndr::RenderContext`
- `scene_rdl2`, RDL2, `SceneContext`
- geometry, materials, maps, lights, cameras
- render outputs / AOVs / framebuffer access
- progressive rendering, texture resources, motion blur, XPU
- rendering lifecycle and scene updates
- Arras (distributed rendering) session/client API
- MoonRay coding standards

**Do not load this entire directory into context by default.** Search for
the relevant file or section first (e.g. `grep`/`glob` for the topic under
`developer-reference/`), then read only what's needed. This matters for
context efficiency.

Layout:

```text
docs/vendor/openmoonray/
├── README.md                — this file (ours)
├── ATTRIBUTION.md            — license/provenance (ours)
├── UPSTREAM.json             — exact pinned commit metadata (ours)
├── LICENSE-CC-BY-4.0.txt     — upstream license text, copied verbatim
├── developer-reference/      — upstream Markdown docs (vendored, unmodified
│                               except two documented local-link fixes)
└── assets/images/developer-reference/arras/
                              — the one image asset developer-reference/
                                depends on (vendored)
```

Topic map inside `developer-reference/`:

- `index.md` — developer's guide entry point
- `source-structure.md` — repository/source layout
- `scene_rdl2-library.md` — scene_rdl2 / RDL2 overview
- `coding-standards/` — MoonRay C++ coding standards
- `shaders/` — cameras, lights, light-filters, maps, materials,
  normal-maps, displacement, display-filters, volume-shaders,
  geometry-procedurals
- `arras/` — distributed rendering (Arras) client API, session
  definitions, and generated Doxygen HTML for `mcrt_dataio`

## Important limitation

Documentation is **not proof** that an API behaves exactly the same way in
our pinned MoonRay source version. When an implementation decision depends
on an exact API signature, ABI detail, or runtime behavior, verify against
the pinned MoonRay source headers as well — do not infer support from
documentation alone. See the root [`CLAUDE.md`](../../../CLAUDE.md) /
[`AGENTS.md`](../../../AGENTS.md) rule for the required lookup order.

## Refreshing this snapshot

Run [`scripts/sync_openmoonray_docs.py`](../../../scripts/sync_openmoonray_docs.py)
manually and review the resulting diff before committing. This is
intentionally **not** wired into CI — documentation updates must be a
deliberate, reviewed action, not an automatic side effect of a build.
