## What changed

<!-- Concise description. -->

## Why

<!-- Link issue/phase/ADR when relevant. -->

## Architecture impact

- [ ] No architecture boundary change
- [ ] Changes Direct Bridge/add-on protocol or process boundary (ADR may be required)
- [ ] Touches Hydra reference path only

## Validation

<!-- List only tests/commands/results actually observed. -->

## Compatibility evidence

<!-- Exact Blender / Bridge / MoonRay / OS/WSL identities when relevant. -->

## Performance evidence

<!-- Required for performance claims. Include methodology, not just a faster/slower statement. -->

## Checklist

- [ ] I did not make Hydra a required production dependency without an accepted ADR.
- [ ] I did not introduce Python element-by-element bulk geometry/framebuffer transfer for a production path.
- [ ] Tests/evidence cover the changed behavior.
- [ ] Documentation/support matrix is updated when behavior or compatibility changed.
- [ ] No secrets/private assets/build caches are committed.
