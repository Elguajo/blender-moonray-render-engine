# Repository Structure

```text
.
├── addon/                    Blender RenderEngine integration (Phase 05+)
├── bridge/                   Native Direct MoonRay Bridge (Phase 04+)
├── experiments/hydra/        Hydra/hdMoonray fallback/reference/benchmark only
├── .github/                  Issue forms, PR template, CI, release config
├── docs/
│   ├── project/              Canonical outcome/architecture/roadmap/current state
│   ├── phases/               Phase execution specs
│   ├── completions/          Observed completion records
│   ├── decisions/            ADRs
│   ├── research/             Source-backed research
│   ├── design/               Non-canonical detailed target designs
│   ├── runbooks/             Operator procedures
│   ├── evidence/             Shareable evidence/templates
│   └── maintainers/          Repository administration
├── scripts/                  Host/build/validation/maintenance helpers
├── AGENTS.md                 Codex/general agent entry point
├── CLAUDE.md                 Claude Code entry point
├── AGENT_HANDOFF.md          Shared continuation contract
└── LICENSE
```

Do not commit build trees, upstream source mirrors, downloaded archives, render caches or large generated outputs.
