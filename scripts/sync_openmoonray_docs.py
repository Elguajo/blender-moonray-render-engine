#!/usr/bin/env python3
"""Sync the vendored OpenMoonRay developer-reference documentation.

Fetches `docs/developer-reference/` (plus the minimum set of assets it
depends on) from the official `OpenMoonRay/openmoonray-docs` repository and
atomically replaces the local vendored snapshot under
`docs/vendor/openmoonray/`.

This script is intentionally NOT run automatically in CI. Documentation
updates must be an intentional, reviewed action:

    python scripts/sync_openmoonray_docs.py

Then inspect `git diff` before committing.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM_REPO = "https://github.com/OpenMoonRay/openmoonray-docs"
SOURCE_SUBPATH = "docs/developer-reference"
WEBSITE = "https://docs.openmoonray.org/developer-reference/"
LICENSE_ID = "CC-BY-4.0"

REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = REPO_ROOT / "docs" / "vendor" / "openmoonray"
DEV_REF_DIRNAME = "developer-reference"

# Asset-like extensions that count as a real dependency worth vendoring.
# Markdown/HTML page targets are treated as cross-references, not
# dependencies, and are intentionally left unvendored and unmodified.
ASSET_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".css", ".js", ".pdf",
}

LIQUID_ABSOLUTE_URL_RE = re.compile(
    r'\{\{\s*["\']([^"\']+)["\']\s*\|\s*absolute_url\s*\}\}'
)
MD_LINK_RE = re.compile(r'\]\(([^)\s]+)\)')


@dataclass
class Dependency:
    """An asset dependency discovered outside developer-reference/."""
    # Path relative to the upstream repo's docs/ root, e.g.
    # "assets/images/developer-reference/arras/arras-session-diagram.png"
    docs_relative_path: str
    # Files (relative to developer-reference/) that reference it, and the
    # exact liquid/markdown snippet used, so links can be rewritten.
    referenced_by: list[tuple[str, str]] = field(default_factory=list)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def clone_upstream(dest: Path, branch: str | None) -> tuple[str, str]:
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [UPSTREAM_REPO, str(dest)]
    print(f"Cloning {UPSTREAM_REPO} ({'branch ' + branch if branch else 'default branch'})...")
    # docs/developer-reference/ itself is not LFS-tracked upstream, but
    # docs/assets/** (where its one image dependency lives) is. Skip the LFS
    # smudge on clone -- the whole repo's LFS payload is hundreds of MB --
    # and pull only the specific objects actually needed afterward.
    import os
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    sha = run(["git", "-C", str(dest), "rev-parse", "HEAD"]).stdout.strip()
    actual_branch = run(
        ["git", "-C", str(dest), "rev-parse", "--abbrev-ref", "HEAD"]
    ).stdout.strip()
    return sha, actual_branch


def materialize_lfs_pointers(clone_dir: Path, docs_relative_paths: list[str]) -> None:
    """Pull real content for specific LFS-tracked paths only (avoids
    downloading the repository's full, largely unrelated, LFS payload)."""
    targets = []
    for rel in docs_relative_paths:
        path = clone_dir / "docs" / rel
        if not path.is_file():
            continue
        head = path.open("rb").read(64)
        if head.startswith(b"version https://git-lfs.github.com/spec"):
            targets.append(f"docs/{rel}")
    if not targets:
        return
    print(f"Pulling {len(targets)} LFS object(s) needed by developer-reference/...")
    run(["git", "-C", str(clone_dir), "lfs", "pull", "--include", ",".join(targets)])


def find_dependencies(dev_ref_src: Path, docs_root: Path) -> dict[str, Dependency]:
    """Scan developer-reference markdown for asset references that live
    outside developer-reference/, resolved against the upstream docs/ root."""
    deps: dict[str, Dependency] = {}

    for md_file in dev_ref_src.rglob("*.md"):
        rel_md = md_file.relative_to(dev_ref_src).as_posix()
        text = md_file.read_text(encoding="utf-8", errors="replace")

        # 1. Jekyll `{{ "/site/relative/path" | absolute_url }}` references.
        for match in LIQUID_ABSOLUTE_URL_RE.finditer(text):
            site_path = match.group(1)
            if not site_path.startswith("/"):
                continue
            candidate = docs_root / site_path.lstrip("/")
            if candidate.suffix.lower() in ASSET_EXTENSIONS and candidate.is_file():
                docs_rel = candidate.relative_to(docs_root).as_posix()
                if docs_rel.startswith(SOURCE_SUBPATH.split("/", 1)[1] + "/"):
                    continue  # already inside developer-reference
                deps.setdefault(docs_rel, Dependency(docs_rel)).referenced_by.append(
                    (rel_md, match.group(0))
                )

        # 2. Plain markdown links, either site-root-relative ("/...") or
        #    relative ("../../...") that resolve outside developer-reference.
        for match in MD_LINK_RE.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "#", "{{")):
                continue
            if target.startswith("/"):
                candidate = docs_root / target.lstrip("/")
            elif target.startswith(".."):
                candidate = (md_file.parent / target).resolve()
            else:
                continue  # same-directory / within-tree relative link
            try:
                docs_rel = candidate.resolve().relative_to(docs_root.resolve()).as_posix()
            except ValueError:
                continue  # points outside the docs/ tree entirely; ignore
            if docs_rel.startswith(SOURCE_SUBPATH.split("/", 1)[1] + "/"):
                continue  # inside developer-reference already
            if candidate.suffix.lower() not in ASSET_EXTENSIONS or not candidate.is_file():
                continue  # a cross-reference to another page, not an asset
            deps.setdefault(docs_rel, Dependency(docs_rel)).referenced_by.append(
                (rel_md, match.group(0))
            )

    return deps


def stage_snapshot(dev_ref_src: Path, docs_root: Path, deps: dict[str, Dependency],
                    staging: Path) -> list[dict]:
    """Copy developer-reference/ and its dependencies into a staging dir,
    rewriting only the exact links required to resolve vendored assets
    locally. Returns the list of applied local-link modifications."""
    dev_ref_dst = staging / DEV_REF_DIRNAME
    shutil.copytree(dev_ref_src, dev_ref_dst)

    modifications = []
    for docs_rel, dep in deps.items():
        src_asset = docs_root / docs_rel
        dst_asset = staging / docs_rel
        dst_asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_asset, dst_asset)

        for rel_md, snippet in dep.referenced_by:
            md_path = dev_ref_dst / rel_md
            text = md_path.read_text(encoding="utf-8")
            if snippet not in text:
                continue
            rel_link = _relative_link(md_path.parent, dst_asset)
            # Only rewrite image/link markdown; preserve the surrounding
            # `![alt](...)` / `[text](...)` shape, replace just the URL part.
            new_snippet = re.sub(r'\([^)]*\)\Z', f'({rel_link})', snippet) \
                if snippet.startswith("[") or snippet.startswith("!") \
                else rel_link
            if new_snippet == snippet:
                continue
            new_text = text.replace(snippet, new_snippet)
            if new_text != text:
                md_path.write_text(new_text, encoding="utf-8")
                modifications.append({
                    "file": f"{DEV_REF_DIRNAME}/{rel_md}",
                    "before": snippet,
                    "after": new_snippet,
                    "reason": "Jekyll liquid/site-relative reference rewritten to a "
                              "plain relative Markdown path so the vendored asset "
                              "resolves outside the Jekyll build.",
                })
    return modifications


def _relative_link(from_dir: Path, to_file: Path) -> str:
    import os
    return Path(os.path.relpath(to_file, start=from_dir)).as_posix()


def diff_trees(old: Path, new: Path) -> tuple[list[str], list[str], list[str]]:
    """Return (added, removed, changed) file lists, relative paths, comparing
    two directory trees (developer-reference + vendored assets only)."""
    added, removed, changed = [], [], []

    def walk(base: Path) -> set[str]:
        if not base.is_dir():
            return set()
        return {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}

    old_files = walk(old)
    new_files = walk(new)
    added = sorted(new_files - old_files)
    removed = sorted(old_files - new_files)
    for rel in sorted(old_files & new_files):
        if not filecmp.cmp(old / rel, new / rel, shallow=False):
            changed.append(rel)
    return added, removed, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", default=None,
                         help="Upstream branch to clone (default: repo's default branch)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Report what would change without writing anything")
    args = parser.parse_args()

    previous_commit = None
    upstream_json_path = VENDOR_ROOT / "UPSTREAM.json"
    if upstream_json_path.is_file():
        previous_commit = json.loads(upstream_json_path.read_text(encoding="utf-8")).get("commit")

    with tempfile.TemporaryDirectory(prefix="openmoonray-docs-") as tmp:
        clone_dir = Path(tmp) / "clone"
        sha, branch = clone_upstream(clone_dir, args.branch)

        docs_root = clone_dir / "docs"
        dev_ref_src = docs_root / DEV_REF_DIRNAME
        if not dev_ref_src.is_dir():
            print(f"ERROR: {SOURCE_SUBPATH} not found in upstream clone", file=sys.stderr)
            return 1

        license_src = clone_dir / "LICENSE"

        deps = find_dependencies(dev_ref_src, docs_root)
        print(f"Discovered {len(deps)} asset dependency(ies) outside developer-reference/:")
        for docs_rel in deps:
            print(f"  - {docs_rel}")
        materialize_lfs_pointers(clone_dir, list(deps.keys()))

        staging = Path(tmp) / "staging"
        staging.mkdir()
        modifications = stage_snapshot(dev_ref_src, docs_root, deps, staging)

        old_dev_ref = VENDOR_ROOT / DEV_REF_DIRNAME
        added, removed, changed = diff_trees(old_dev_ref, staging / DEV_REF_DIRNAME)
        for docs_rel in deps:
            old_asset = VENDOR_ROOT / docs_rel
            new_asset = staging / docs_rel
            rel = f"{docs_rel} (extra asset)"
            if not old_asset.is_file():
                added.append(rel)
            elif not filecmp.cmp(old_asset, new_asset, shallow=False):
                changed.append(rel)

        print()
        print(f"Previous commit: {previous_commit or '(none — first import)'}")
        print(f"New commit:      {sha}")
        print(f"Added files:     {len(added)}")
        print(f"Removed files:   {len(removed)}")
        print(f"Changed files:   {len(changed)}")

        if args.dry_run:
            print("\n--dry-run: no files were written.")
            return 0

        if previous_commit == sha and not added and not removed and not changed:
            print("\nAlready up to date; nothing to do.")
            return 0

        # Atomic replace: build the full new vendor tree alongside the old
        # one, then swap.
        new_vendor = Path(tmp) / "new_vendor"
        new_vendor.mkdir()
        shutil.copytree(staging / DEV_REF_DIRNAME, new_vendor / DEV_REF_DIRNAME)
        for docs_rel in deps:
            dst = new_vendor / docs_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staging / docs_rel, dst)
        shutil.copy2(license_src, new_vendor / "LICENSE-CC-BY-4.0.txt")

        # Preserve our own hand-authored files if present.
        for ours in ("README.md", "ATTRIBUTION.md"):
            src = VENDOR_ROOT / ours
            if src.is_file():
                shutil.copy2(src, new_vendor / ours)

        upstream_json = {
            "project": "OpenMoonRay Documentation",
            "repository": UPSTREAM_REPO,
            "source_path": SOURCE_SUBPATH,
            "extra_source_paths": sorted(deps.keys()),
            "website": WEBSITE,
            "license": LICENSE_ID,
            "branch": branch,
            "commit": sha,
            "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "imported_file_count": sum(1 for _ in (new_vendor / DEV_REF_DIRNAME).rglob("*") if _.is_file()),
            "extra_asset_file_count": len(deps),
            "local_link_modifications": modifications,
        }
        (new_vendor / "UPSTREAM.json").write_text(
            json.dumps(upstream_json, indent=2) + "\n", encoding="utf-8"
        )

        backup = VENDOR_ROOT.parent / f"{VENDOR_ROOT.name}.bak"
        if VENDOR_ROOT.is_dir():
            if backup.exists():
                shutil.rmtree(backup)
            VENDOR_ROOT.rename(backup)
        try:
            shutil.move(str(new_vendor), str(VENDOR_ROOT))
        except Exception:
            if backup.exists() and not VENDOR_ROOT.exists():
                backup.rename(VENDOR_ROOT)
            raise
        else:
            if backup.exists():
                shutil.rmtree(backup)

    print(f"\nVendored snapshot updated at {VENDOR_ROOT}")
    print("Review `git diff` before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
