#!/usr/bin/env python3
"""Overlay this MoonRay project checkpoint into an installed Progressive Context Runtime."""
from __future__ import annotations
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".progressive"

if not RUNTIME.exists():
    print("ERROR: .progressive/ not found.")
    print("Install the official Progressive Context Project Runtime first; see handoff/PROGRESSIVE_CONTEXT_RUNTIME_SETUP.md")
    sys.exit(2)

pairs = [
    (ROOT / "docs" / "project", RUNTIME / "project"),
    (ROOT / "docs" / "phases", RUNTIME / "phases"),
    (ROOT / "docs" / "completions", RUNTIME / "completions"),
    (ROOT / "docs" / "decisions", RUNTIME / "decisions"),
]

for src, dst in pairs:
    if not src.exists():
        continue
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        print(f"COPY {p.relative_to(ROOT)} -> {out.relative_to(ROOT)}")

# We intentionally do not overwrite the Runtime's CONTEXT_MANIFEST.json with the
# project-only hint file because Runtime schema may evolve. Codex can read the
# project hint from docs/project/CONTEXT_MANIFEST.project.json when useful.
print("\nProgressive project state overlay complete.")
print("Current phase should be Phase 02; verify .progressive/project/ROADMAP.md before work.")
