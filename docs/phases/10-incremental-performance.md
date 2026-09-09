# Phase 10 — Incremental updates, benchmark and performance hardening

Status: PLANNED

## Goal
Make interactive updates efficient, quantify bottlenecks, and compare Direct Bridge against available Hydra/reference path where a fair comparison can be constructed.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Change classification and incremental scene updates.
- Geometry/material/camera delta strategies.
- Shared-memory/binary transport optimization.
- CPU/memory/latency instrumentation.
- Direct-vs-Hydra benchmark only when comparable.
- Cache invalidation policy.

## Out of scope
- Inventing performance claims without data.
- Premature in-process rewrite.

## Tasks
- [ ] Create representative benchmark scenes.
- [ ] Measure full sync vs delta sync.
- [ ] Measure control/serialization/transport/MoonRay prep/render/display separately.
- [ ] Optimize dominant measured costs.
- [ ] Record reproducible benchmark methodology.
- [ ] Consider in-process experiment only if evidence warrants ADR.

## Acceptance criteria
- [ ] Defined interaction/first-pixel/update latency targets are met or explicitly classified PARTIAL.
- [ ] No major avoidable Python bulk-data bottleneck remains.
- [ ] Performance claims have reproducible benchmark evidence.
- [ ] Hydra comparison is labeled fairly or omitted if non-comparable.

## Verification
- Benchmark scripts/results.
- Profiler evidence.
- Regression thresholds where stable.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/10-incremental-performance.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
