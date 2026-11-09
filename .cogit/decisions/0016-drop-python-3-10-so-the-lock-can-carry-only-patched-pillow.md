---
template: adr
state: Proposed
authority: [human]
date: 2026-11-09
from: {node: release/deps, step: s1}
applies: [release/deps]
---

# Drop Python 3.10 so the lock can carry only patched Pillow

## Background

GitHub's Dependabot reports 45 open alerts on main, all against `uv.lock`:
41 for Pillow (#82-#90, #93-#124; four critical), three for urllib3 and
one for certifi. Pillow is not a direct dependency of detk; it comes in
through matplotlib. For every Pillow alert the first patched release is
Pillow 13.0.0, and Pillow 13.0.0 requires Python >= 3.11.

detk says it supports Python 3.10: `requires-python = ">=3.10"` in
`pyproject.toml`, the 3.10 classifier, "detk requires Python 3.10 or
newer" in the README, and 3.10 in the CI test matrix. uv must lock a
version that installs on every Python the project admits, so
`uv lock --upgrade-package pillow` now forks: Pillow 13.0.0 for Python
>= 3.11 and Pillow 12.3.0 (vulnerable) for Python 3.10. Dependabot reads
every version in the lock, so the 41 Pillow alerts stay open while
12.3.0 is in it. The certifi and urllib3 alerts close with the lock
update on #53 alone.

## Context

- release/deps' acceptance says the Pillow and certifi alerts on main are
  closed by the update; that cannot hold for Pillow without a change to
  the Python versions detk supports.
- Supported Python versions are part of what users and packagers rely
  on, and DETK-0001 (Proposed) makes 1.0 an interface promise; that is
  beyond release/deps' scope (`uv.lock`, `pyproject.toml`'s pins) and so
  the human's call.
- Python 3.10 reached end of life in October 2026, so upstream no longer
  ships security fixes for it either.
- Criteria: close the alerts; keep the support promise honest; least
  churn before the 1.0 cut.

## Options

### Option A: drop Python 3.10 for 1.0 (recommended)

Raise `requires-python` to `>=3.11`, drop the 3.10 classifier, the README
line and the 3.10 CI job, and relock. The lock then carries only Pillow
13.0.0 and all 41 alerts close. Matches 3.10's end of life; 1.0 starts
its promise on supported Pythons. Touches files beyond this node's scope
(README, CI), so it would be a small follow-up on this PR or its own
node.

### Option B: keep Python 3.10 and dismiss the Pillow alerts for 3.10

Leave the fork in the lock and dismiss the 41 alerts as "tolerable risk"
(Pillow on 3.10 only, used by matplotlib for writing figures). Keeps 3.10
users, but ships 1.0 with a known-vulnerable dependency on one Python and
leaves alerts to re-triage.

### Option C: keep Python 3.10 and leave the alerts open

No change; the alerts stay open until 3.10 is dropped later. Least work,
but release/deps' acceptance is not met.

## Decision

Pending Adam's answer. Recommended: Option A, since 3.10 is past end of
life and 1.0 is the natural point to set the floor.

## Consequences

Under A: 3.10 users stay on 0.9.x; follow-up edits `pyproject.toml`
(`requires-python`, classifier), README, `.github/workflows/ci.yml` and
`uv.lock`. Under B or C: release/deps' acceptance is amended to the
certifi and urllib3 alerts, and the Pillow alerts are revisited when 3.10
is dropped.
