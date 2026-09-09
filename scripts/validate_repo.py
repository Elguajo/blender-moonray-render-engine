from pathlib import Path
import re, sys
root = Path(__file__).resolve().parents[1]
errors=[]
required=['README.md','LICENSE','CONTRIBUTING.md','SECURITY.md','AGENTS.md','CLAUDE.md','AGENT_HANDOFF.md','docs/project/PROJECT_BRIEF.md','docs/project/ARCHITECTURE.md','docs/project/ROADMAP.md','docs/project/NEXT_SESSION.md','docs/decisions/ADR-0002-direct-moonray-bridge-primary.md']
for rel in required:
    if not (root/rel).is_file(): errors.append(f'missing required file: {rel}')
road=(root/'docs/project/ROADMAP.md').read_text(encoding='utf-8')
active=re.findall(r'^- \[>\].*?`([^`]+)`',road,re.M)
if len(active)!=1: errors.append(f'expected exactly one active [>] phase, found {len(active)}')
refs=re.findall(r'`(docs/phases/[^`]+\.md)`',road)
if not refs: errors.append('roadmap has no phase file references')
for rel in refs:
    if not (root/rel).is_file(): errors.append(f'roadmap references missing phase: {rel}')
arch=(root/'docs/project/ARCHITECTURE.md').read_text(encoding='utf-8')
if 'Direct' not in arch or 'moonray_bridge' not in arch: errors.append('architecture does not identify Direct Bridge target')
if 'reference/fallback/benchmark' not in arch: errors.append('architecture does not classify Hydra as non-primary')
for rel in ['.github/ISSUE_TEMPLATE/bug.yml','.github/ISSUE_TEMPLATE/compatibility.yml','.github/ISSUE_TEMPLATE/performance.yml','.github/ISSUE_TEMPLATE/feature.yml','.github/ISSUE_TEMPLATE/docs.yml','.github/pull_request_template.md']:
    if not (root/rel).is_file(): errors.append(f'missing GitHub contribution file: {rel}')

# Vendored OpenMoonRay developer-reference documentation (docs/vendor/openmoonray/).
import json
vendor = root/'docs/vendor/openmoonray'
if not vendor.is_dir():
    errors.append('missing vendored docs directory: docs/vendor/openmoonray')
else:
    upstream_json = vendor/'UPSTREAM.json'
    if not upstream_json.is_file():
        errors.append('missing docs/vendor/openmoonray/UPSTREAM.json')
    else:
        try:
            meta = json.loads(upstream_json.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            errors.append(f'docs/vendor/openmoonray/UPSTREAM.json is not valid JSON: {e}')
            meta = {}
        commit = meta.get('commit', '')
        if not re.fullmatch(r'[0-9a-f]{40}', commit or ''):
            errors.append(f'docs/vendor/openmoonray/UPSTREAM.json commit is not a valid 40-char Git SHA: {commit!r}')
        if meta.get('license') != 'CC-BY-4.0':
            errors.append('docs/vendor/openmoonray/UPSTREAM.json does not record license CC-BY-4.0')
    if not (vendor/'ATTRIBUTION.md').is_file():
        errors.append('missing docs/vendor/openmoonray/ATTRIBUTION.md')
    if not any((vendor/n).is_file() for n in ('LICENSE-CC-BY-4.0.txt', 'LICENSE')):
        errors.append('missing vendored CC-BY-4.0 license text under docs/vendor/openmoonray/')
    dev_ref = vendor/'developer-reference'
    if not dev_ref.is_dir() or not any(dev_ref.rglob('*.md')):
        errors.append('docs/vendor/openmoonray/developer-reference/ is missing or empty')
    if (vendor/'.git').exists():
        errors.append('accidentally vendored .git directory under docs/vendor/openmoonray')
    vendor_bytes = sum(f.stat().st_size for f in vendor.rglob('*') if f.is_file())
    if vendor_bytes > 50 * 1024 * 1024:
        errors.append(f'docs/vendor/openmoonray is unexpectedly large ({vendor_bytes} bytes) - possible accidental full-site import')
    site_output_markers = ('_site', 'node_modules', '.jekyll-cache')
    for marker in site_output_markers:
        if any(vendor.rglob(marker)):
            errors.append(f'docs/vendor/openmoonray contains a generated site-output directory: {marker}')
    # Vendored content must not leak into non-vendor project doc locations.
    stray = root/'docs/developer-reference'
    if stray.exists():
        errors.append('vendored-looking docs/developer-reference exists outside docs/vendor/openmoonray')

if errors:
    print('Repository validation: FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('Repository validation: PASS')
print(f'Active phase: {active[0] if active else "NONE"}')
print(f'Roadmap phase specs: {len(refs)}')
