#!/usr/bin/env python3
"""Verify SOURCE_INDEX.md against the upstream commits pinned in
UPSTREAM_LOCK.json.

SOURCE_INDEX.md points at files inside `moonray` and `scene_rdl2` that are
NOT vendored into this repository (see UPSTREAM_LOCK.json). Because those
repos are under active development, a path that's correct today can move or
disappear upstream. This script re-fetches the real file tree at the exact
pinned commits and checks:

  1. every `moonray/...` / `scene_rdl2/...` path referenced in
     SOURCE_INDEX.md still exists at the pinned commit;
  2. the commit table and permalink SHAs embedded in SOURCE_INDEX.md match
     what UPSTREAM_LOCK.json currently pins (catches "lock file was bumped,
     index doc wasn't").

Needs network access (GitHub REST API) - NOT run automatically in CI, same
policy as scripts/sync_openmoonray_docs.py. Run manually:

    python scripts/verify_source_index.py

Exit code 0 = every referenced path verified against the pinned commit.
Exit code 1 = drift found (stale path, or index doc out of sync with the
lock file) - fix SOURCE_INDEX.md (and re-run) before trusting it.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / "UPSTREAM_LOCK.json"
INDEX_PATH = REPO_ROOT / "SOURCE_INDEX.md"

GITHUB_API = "https://api.github.com"
# The upstream repos SOURCE_INDEX.md is allowed to reference paths from.
TRACKED_REPOS = {
    "moonray": "OpenMoonRay/moonray",
    "scene_rdl2": "OpenMoonRay/scene_rdl2",
}

FULL_PATH_RE = re.compile(r"^(moonray|scene_rdl2)/(.+)$")
BARE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_]+\.(h|hh|cc|cpp|ispc|isph|mm)$")
EXT_ONLY_RE = re.compile(r"^\.[A-Za-z0-9]+$")
BACKTICK_RE = re.compile(r"`([^`]+)`")
PERMALINK_RE = re.compile(
    r"github\.com/OpenMoonRay/(moonray|scene_rdl2)/blob/([0-9a-f]{40})/"
)
TABLE_ROW_RE = re.compile(
    r"\[OpenMoonRay/(moonray|scene_rdl2)\]\([^)]+\)\s*\|\s*`([0-9a-f]{40})`"
)


def gh_token() -> str | None:
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def fetch_tree(repo: str, sha: str, token: str | None) -> set[str]:
    url = f"{GITHUB_API}/repos/{repo}/git/trees/{sha}?recursive=1"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API request failed for {repo}@{sha}: {e}") from e
    if data.get("truncated"):
        print(f"WARNING: tree listing for {repo}@{sha} was truncated by the API", file=sys.stderr)
    return {item["path"] for item in data.get("tree", []) if item["type"] == "blob"}


def extract_referenced_paths(text: str) -> set[tuple[str, str]]:
    """Return {(repo_key, path_within_repo)} referenced via backtick spans."""
    results: set[tuple[str, str]] = set()
    current_dir: str | None = None
    current_repo: str | None = None
    current_stem: str | None = None

    for line in text.splitlines():
        # Reset "current file" context at each list item / table row boundary
        # so unrelated bullets never inherit each other's directory.
        if line.strip().startswith("-") or line.strip().startswith("|"):
            current_dir = current_repo = current_stem = None

        for token in BACKTICK_RE.findall(line):
            m = FULL_PATH_RE.match(token)
            if m:
                repo_key, rel = m.group(1), m.group(2)
                current_repo, current_dir = repo_key, Path(rel).parent.as_posix()
                current_stem = Path(rel).stem
                results.add((repo_key, rel))
                continue
            if EXT_ONLY_RE.match(token) and current_repo and current_stem is not None:
                rel = f"{current_stem}{token}" if current_dir in (None, ".") else f"{current_dir}/{current_stem}{token}"
                results.add((current_repo, rel))
                continue
            if BARE_FILENAME_RE.match(token) and current_repo:
                rel = token if current_dir in (None, ".") else f"{current_dir}/{token}"
                current_stem = Path(token).stem
                results.add((current_repo, rel))
                continue
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()

    errors: list[str] = []

    if not LOCK_PATH.is_file():
        print(f"ERROR: missing {LOCK_PATH}", file=sys.stderr)
        return 1
    if not INDEX_PATH.is_file():
        print(f"ERROR: missing {INDEX_PATH}", file=sys.stderr)
        return 1

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    pins: dict[str, str] = {}
    for repo_key, gh_repo in TRACKED_REPOS.items():
        entry = lock.get(repo_key) or {}
        sha = entry.get("commit")
        if not sha or not re.fullmatch(r"[0-9a-f]{40}", sha):
            errors.append(f"UPSTREAM_LOCK.json: {repo_key}.commit is missing or not a 40-char SHA")
            continue
        pins[repo_key] = sha

    # 1. Doc's commit table / permalinks must match the lock file exactly.
    for repo_key, sha in TABLE_ROW_RE.findall(index_text):
        if repo_key in pins and sha != pins[repo_key]:
            errors.append(
                f"SOURCE_INDEX.md commit table shows {repo_key}@{sha} but "
                f"UPSTREAM_LOCK.json pins {pins[repo_key]} - regenerate the index"
            )
    for repo_key, sha in PERMALINK_RE.findall(index_text):
        if repo_key in pins and sha != pins[repo_key]:
            errors.append(
                f"SOURCE_INDEX.md permalink uses {repo_key}@{sha} but "
                f"UPSTREAM_LOCK.json pins {pins[repo_key]} - regenerate the index"
            )

    if errors:
        # Pin mismatch makes path verification below meaningless (we'd be
        # checking the wrong commit); report now and stop.
        print("Source index verification: FAIL")
        for e in errors:
            print("-", e)
        return 1

    # 2. Every referenced path must exist at the pinned commit.
    referenced = extract_referenced_paths(index_text)
    by_repo: dict[str, set[str]] = {}
    for repo_key, rel in referenced:
        by_repo.setdefault(repo_key, set()).add(rel)

    token = gh_token()
    trees: dict[str, set[str]] = {}
    for repo_key in by_repo:
        gh_repo = TRACKED_REPOS[repo_key]
        sha = pins[repo_key]
        print(f"Fetching {gh_repo}@{sha[:12]} tree ({len(by_repo[repo_key])} paths to check)...")
        try:
            trees[repo_key] = fetch_tree(gh_repo, sha, token)
        except RuntimeError as e:
            errors.append(str(e))

    for repo_key, paths in sorted(by_repo.items()):
        tree = trees.get(repo_key)
        if tree is None:
            continue
        for rel in sorted(paths):
            if rel not in tree:
                errors.append(f"{repo_key}/{rel} not found at pinned commit {pins[repo_key]}")

    total_checked = sum(len(p) for p in by_repo.values())
    if errors:
        print("\nSource index verification: FAIL")
        for e in errors:
            print("-", e)
        return 1

    print(f"\nSource index verification: PASS ({total_checked} paths checked across {len(by_repo)} repo(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
