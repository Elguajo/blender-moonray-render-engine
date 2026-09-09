# Attribution — Vendored OpenMoonRay Documentation

Everything under `docs/vendor/openmoonray/developer-reference/` and
`docs/vendor/openmoonray/assets/` is a vendored copy of third-party content.
It is **not** original work of this project.

- **Project:** OpenMoonRay Documentation
- **Upstream repository:** <https://github.com/OpenMoonRay/openmoonray-docs>
- **Documentation website:** <https://docs.openmoonray.org/>
- **Developer Reference:** <https://docs.openmoonray.org/developer-reference/>
- **Copyright:** the respective MoonRay / OpenMoonRay contributors (DreamWorks
  Animation LLC and the Academy Software Foundation / OpenMoonRay project
  community).
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
  Full license text: [LICENSE-CC-BY-4.0.txt](LICENSE-CC-BY-4.0.txt) (copied
  verbatim from the upstream repository's `LICENSE` file).

This repository contains a vendored, pinned snapshot of the upstream
`docs/developer-reference/` tree for offline development-reference purposes
only. See [UPSTREAM.json](UPSTREAM.json) for the exact imported commit,
branch, and timestamp.

## No affiliation / no endorsement

This project is **not affiliated with or endorsed by** DreamWorks Animation,
OpenMoonRay, the Academy Software Foundation (ASWF), the Blender Foundation,
or the Linux Foundation, unless explicitly stated otherwise.

## Scope of this vendored copy

Only `docs/developer-reference/` from the upstream repository was imported,
plus the single image asset it depends on
(`docs/assets/images/developer-reference/arras/arras-session-diagram.png`,
copied to `assets/images/developer-reference/arras/arras-session-diagram.png`
in this vendor tree to preserve its relative path under the upstream `docs/`
root). The upstream repository also contains `getting-started/`,
`user-reference/`, `style-reference/`, `geometry/`, `api/`, Jekyll site
scaffolding, and other material that is **not** vendored here because
`docs/developer-reference/` does not depend on it. See `UPSTREAM.json` for
the full dependency-inspection notes.

## Modifications from upstream

The vendored copy is intended to remain recognizably identical to upstream.
The **only** content changes made are two Jekyll-liquid image links rewritten
to plain relative Markdown paths so the one vendored image renders outside of
a Jekyll build. See the `local_link_modifications` entry in
[UPSTREAM.json](UPSTREAM.json) for the exact before/after text. No other
prose, code examples, or structure were altered, rewritten, or "improved."

Some links that point outside `docs/developer-reference/` (to pages this
project intentionally does not vendor, such as `getting-started/` or
`user-reference/` pages) are left as unresolved Jekyll liquid tags or
relative paths — see `known_unresolved_links` in `UPSTREAM.json`. Follow
those links on <https://docs.openmoonray.org/> if you need that content.

## How to refresh this snapshot

Use [`scripts/sync_openmoonray_docs.py`](../../../scripts/sync_openmoonray_docs.py).
Documentation updates are intentional and reviewed — this script is **not**
run automatically in CI.
