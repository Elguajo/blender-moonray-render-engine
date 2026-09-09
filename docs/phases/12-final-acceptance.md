# Phase 12 — Production acceptance, known limitations and release archive

Status: PLANNED

## Goal
Perform final production acceptance, publish explicit compatibility/limitations, and create a release-ready archive/checkpoint.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Full acceptance matrix.
- Known limitations.
- Operator guide.
- Contributor/developer guide.
- Version pins/checksums.
- Release archive and manifest.
- Security/license/NOTICE review.

## Out of scope
- Expanding feature scope after acceptance begins without new change request.

## Tasks
- [ ] Run final fixture suite on clean validated environment.
- [ ] Review every Must-have success criterion.
- [ ] Generate compatibility/feature PASS-PARTIAL-FAIL matrix.
- [ ] Generate archive manifest/checksums.
- [ ] Validate repo/CI/docs links.

## Acceptance criteria
- [ ] All mandatory success criteria PASS or user explicitly accepts documented PARTIALs.
- [ ] No UNKNOWN remains for mandatory production path.
- [ ] Archive recreates the documented project state.
- [ ] Release docs accurately separate supported/experimental/unsupported behavior.

## Verification
- Final clean-environment run.
- Repository validator/CI.
- Archive checksum/manifest verification.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/12-final-acceptance.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
