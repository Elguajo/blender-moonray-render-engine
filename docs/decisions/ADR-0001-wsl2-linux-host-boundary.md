# ADR-0001 — Windows host with WSL2/WSLg Linux execution boundary

Status: ACCEPTED
Date: 2026-09-08

## Context
MoonRay's supported/open build environment is Linux/macOS-oriented while the operator requires Windows 11 as the workstation environment. Native Windows Blender cannot directly consume Linux MoonRay binaries.

## Decision
Use **Windows 11 + WSL2/WSLg** as the workstation/runtime boundary, running Linux Blender and renderer-side native components inside WSL2. Rocky Linux 9.x is the initial distro family to validate.

## Consequences
- Windows remains the operator desktop.
- Blender/MoonRay-facing native runtime shares a Linux environment.
- WSLg provides the Blender GUI.
- GPU support must be validated through WSL-supported driver paths; no unsupported Linux display-driver installation inside WSL.
- Dedicated Linux remains fallback if WSL2 later fails production criteria.

## Supersession note
The original Phase 01 architecture also selected Hydra/hdMoonray as primary integration. **ADR-0002 supersedes that renderer-integration portion only.** This ADR remains authoritative for the Windows→WSL2 host boundary.
