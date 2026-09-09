# Progressive Context Runtime Setup for Codex

The project checkpoint is project-owned state. The recommended Codex workspace uses the official Progressive Context Project Runtime v2.0.0.

## 1. Download the official Runtime
From `Elguajo/Progressive-Context-Kit` release `v2.0.0`, download:

`Progressive-Context-Project-Runtime-v2.0.0.zip`

Published asset SHA256:

`218d9eb9667b367f47501d57f807b0c6a27bbd890de3e397b9e3342bf8b7e23e`

Do not extract Framework Source over this project; use the Project Runtime asset.

## 2. Extract Runtime into project root
The Runtime provides root `AGENTS.md`, agent Skills and `.progressive/` protocols/tools.

## 3. Overlay this checkpoint's canonical state
From project root run:

```bash
python scripts/bootstrap_progressive_runtime.py
```

The script copies:
- `docs/project/*` → `.progressive/project/*`
- `docs/phases/*` → `.progressive/phases/*`
- `docs/completions/*` → `.progressive/completions/*`
- `docs/decisions/*` → `.progressive/decisions/*`

Research, runbooks, evidence and product scripts stay under `docs/` / `scripts/` because they are project-owned artifacts.

## 4. Open the root directory in Codex
Paste `handoff/CODEX_START_PROMPT.txt` as the first instruction.

## Important
If the installed Runtime version is newer than 2.0.0, first follow the Kit's official runtime-update/adoption guidance. Do not blindly replace project-owned state.
