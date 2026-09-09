# Governance

The project currently uses a maintainer-led model.

## Maintainers

Maintainers are responsible for:

- roadmap and architecture decisions;
- review and merge decisions;
- release/version pins;
- compatibility claims;
- security handling;
- project-state and documentation integrity.

## Decision process

Routine fixes can be decided in Pull Requests. Material changes to architecture, runtime boundaries, upstream version strategy, supported platforms, public interfaces, or licensing should be discussed in an Issue and recorded as an ADR when accepted.

## Compatibility claims

A maintainer may reject or downgrade a compatibility claim that lacks reproducible evidence even when the underlying code appears correct.

## Releases

A release should identify the exact validated Blender/Bridge/MoonRay/platform combination and known limitations. "Works with latest" is not an acceptable release definition.
