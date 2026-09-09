# GitHub Repository Setup

Recommended repository name: **`moonray-blender-bridge`**

Recommended description:
> Community direct integration of OpenMoonRay as a Blender 5.2+ Render Engine on Linux/WSL2. Experimental, production-oriented, not affiliated with DreamWorks or Blender Foundation.

Recommended topics:
```text
blender
moonray
openmoonray
render-engine
renderer
rendering
rdl2
wsl2
linux
vfx
3d
cpp
python
```

## Features
Enable Issues, Discussions, Projects (optional), and Private vulnerability reporting.

## Labels
After cloning with GitHub CLI authenticated:
```bash
bash scripts/github/create_labels.sh
```

## Main branch rules
After initial bootstrap/CI exists:
- require PR before merge;
- require `Repository checks / validate`;
- block force pushes/deletion;
- require conversation resolution;
- optionally require one approving review when outside contributors participate.

Recommended merge strategy: **Squash merge**.

## Issues
Structured forms include Bug, Compatibility, Performance, Feature and Documentation. Compatibility and performance are separate because exact builds and measured evidence are central to this project.

## CODEOWNERS
Replace `@YOUR_GITHUB_USERNAME` in `.github/CODEOWNERS.example`, then rename it to `.github/CODEOWNERS`.

## Release naming
Do not call early releases stable. Example checkpoints:
```text
v0.1.0-host-foundation
v0.2.0-moonray-runtime
v0.3.0-direct-bridge
v0.4.0-first-f12
v0.5.0-viewport-preview
```

## Suggested social preview
```text
MoonRay Blender Bridge
Blender RenderEngine ↔ Direct Bridge ↔ MoonRay
WSL2 / Linux • Experimental
```
Avoid upstream logos unless usage terms explicitly permit the intended use.
