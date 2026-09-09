# Phase 00 — Scope, Constraints and Durable Project Baseline

## Goal
Create durable, spec-driven project state that fixes the requested outcome, non-goals, phase gates and initial research boundaries before implementation begins.

## Context
The project starts from a strong requirement: MoonRay must ultimately behave as a Blender render engine on a Windows-hosted production workstation using Blender 5.2+.

## In scope
- Define product outcome, users, must-have scope and explicit non-goals.
- Classify planning depth/complexity/risk.
- Establish project phase sequence and user approval gate between phases.
- Record initial architecture candidates without prematurely accepting one.

## Out of scope
- Installing WSL/Linux/Blender.
- Building MoonRay or hdMoonray.
- Writing Blender integration code.

## Tasks
- [x] Create Project Brief.
- [x] Create baseline Architecture and Roadmap.
- [x] Define phase-by-phase execution and completion discipline.
- [x] Create durable handoff state.

## Acceptance criteria
- [x] Product outcome and non-goals are explicit.
- [x] Exactly one current phase exists after initialization.
- [x] Planning depth is FULL, Complexity L, Risk High.
- [x] Next work is architecture/compatibility validation rather than implementation by assumption.

## Verification
- Manual consistency review across Project Brief, Architecture, Roadmap and NEXT_SESSION.

## Completion Record
Status: COMPLETE
Completed: 2026-09-08
Outcome: Durable project baseline established. Phase 01 became the next approved investigation target.
Handoff: Validate the production host architecture and current Blender/OpenUSD/Hydra/MoonRay compatibility before installation.
