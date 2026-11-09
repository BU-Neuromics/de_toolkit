---
kind: step
time: 2026-11-09T20:06:02Z
by: DETK/developer
node: release/deps
step: s1
branch: node/53-deps
verdict: done
commits: [05a25b4, 635517a, 7ad0b38]
decisions: []
---

# Done: Update uv.lock (`uv lock --upgrade-package pillow --upgrade-package certifi`, and any other package an open alert names), run the suite; open the PR

## Summary

Relocked uv.lock with only patched Pillow 13.0.0 (no Python 3.10 fork) plus certifi 2026.10.23 and urllib3 2.8.0; dropped Python 3.10 per DETK-0016 (requires-python >=3.11, classifier, CI matrix, README/docs/CHANGELOG). pytest 216 passed/49 R skipped on 3.13 and 3.11; ruff, format, mkdocs --strict clean.

## Artifacts

## Findings

## Questions
