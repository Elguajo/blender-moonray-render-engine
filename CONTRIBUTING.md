# Contributing

Thanks for contributing to the Direct MoonRay Render Engine for Blender 5.2+ project.

This is an experimental renderer-integration project where exact versions, reproducibility and observed evidence matter more than assumptions.

## Architecture contract

Primary path:
```text
Blender RenderEngine → Direct local Bridge → MoonRay
```

Hydra/hdMoonray is reference/fallback/benchmark only. A PR that makes Hydra mandatory or embeds MoonRay into Blender's process as the default requires an accepted ADR first.

## Before starting
1. Search existing Issues/Discussions.
2. Read `docs/project/PROJECT_BRIEF.md`, `ARCHITECTURE.md`, `ROADMAP.md` and the relevant current phase.
3. For architecture-sensitive work, reference the applicable ADR.
4. Avoid unrelated refactors/dependency upgrades.

## Evidence rules

### Compatibility claims
Include exact:
- Blender version/build;
- OS/WSL/Linux release;
- MoonRay tag/commit;
- Bridge commit;
- CPU/GPU;
- reproduction steps;
- observed PASS/PARTIAL/FAIL;
- logs/errors where relevant.

### Performance claims
Include:
- scene/test fixture;
- render/update settings;
- warm/cold methodology;
- number of runs;
- hardware/software versions;
- measured wall time/latency/memory as relevant;
- separate translation/transport/render/presentation timing when claiming a bridge bottleneck.

Do **not** submit claims such as "Hydra is slow" or "shared memory is faster" without a reproducible comparison.

## Pull requests
- Keep one coherent purpose per PR.
- Add/update tests/evidence for behavior changes.
- Update docs/support matrix when compatibility changes.
- Do not commit build trees, downloaded upstream archives, private assets, render caches or secrets.
- Preserve GPL-compatible licensing for code linked/embedded into Blender add-on paths; third-party code keeps its license and notice obligations.

## Commit/PR language
Use concise English for code, identifiers, commits and PR titles/descriptions unless an existing repository convention says otherwise.

## Local validation
Run:
```bash
python3 scripts/validate_repo.py
bash -n scripts/linux/*.sh scripts/github/*.sh
```

Additional component tests are added as implementation phases land.

## Security
Do not open a public issue for vulnerabilities. See `SECURITY.md`.
