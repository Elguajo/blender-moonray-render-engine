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
if errors:
    print('Repository validation: FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('Repository validation: PASS')
print(f'Active phase: {active[0] if active else "NONE"}')
print(f'Roadmap phase specs: {len(refs)}')
