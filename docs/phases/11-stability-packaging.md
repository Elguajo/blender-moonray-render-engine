# Phase 11 — Stability, recovery, packaging and installer

Status: PLANNED

## Goal
Turn the validated integration into a repeatable operator package with recovery, diagnostics, upgrade/rollback and clean installation.

## Preconditions
- Previous phase is COMPLETE with persisted evidence.
- User explicitly approved this phase.

## In scope
- Bridge watchdog/restart policy.
- Structured logs.
- Version compatibility handshake.
- Install/update/rollback scripts/package.
- Blender add-on packaging.
- Config/cache locations.
- Crash/soak testing.

## Out of scope
- Calling release stable before Phase 12.
- Automatic unverified dependency upgrades.

## Tasks
- [ ] Run repeated renders/viewport soak.
- [ ] Kill bridge during operations and verify recovery.
- [ ] Test clean install.
- [ ] Test uninstall/rollback.
- [ ] Document troubleshooting and log collection.

## Acceptance criteria
- [ ] Clean environment can install and run accepted baseline.
- [ ] Bridge crashes are recoverable according to documented policy.
- [ ] Rollback works.
- [ ] No manual hidden environment edits are required.
- [ ] Soak/repeatability criteria pass or limits are explicit.

## Verification
- Clean-install evidence.
- Failure-injection tests.
- Soak logs.

## Completion Record
Status: NOT STARTED

When complete, write `docs/completions/11-stability-packaging.md`, update Roadmap/NEXT_SESSION, then STOP for user approval.
