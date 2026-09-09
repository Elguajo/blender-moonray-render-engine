# Hydra / hdMoonray Experiment

Hydra is **not the primary production architecture** after ADR-0002.

This directory exists for:
- fallback experiments if the Direct Bridge hits a blocker;
- standards/reference comparisons;
- controlled performance/feature benchmarking against the Direct Bridge.

Rules:
- do not add Hydra/hdMoonray as a required dependency of `addon/` or `bridge/` without a new accepted ADR;
- do not claim Hydra is slower/faster without comparable benchmark evidence;
- keep experimental scripts/configs isolated here.
