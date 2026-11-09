---
kind: step
time: 2026-11-09T19:50:24Z
by: DETK/developer
node: release/deps
step: s1
branch: node/53-deps
verdict: done
commits: [be99a82, 83f4538]
decisions: [DETK-0016]
---

# Done: Update uv.lock (`uv lock --upgrade-package pillow --upgrade-package certifi`, and any other package an open alert names), run the suite; open the PR

## Summary

uv.lock updated: certifi 2026.7.22 -> 2026.10.23 (alert #125), urllib3 2.7.0 -> 2.8.0 (#80, #81, #91), Pillow 12.3.0 -> 13.0.0 on Python >= 3.11. Pillow 13 needs Python >= 3.11, so the lock keeps 12.3.0 for 3.10 and the 41 Pillow alerts stay open until Adam answers DETK-0016 (drop 3.10?). pyproject.toml unchanged. pytest (3.13 and 3.10) 216 passed/49 skipped, ruff check and format clean, mkdocs --strict builds; R job left to CI.

## Artifacts

## Findings

## Questions

- DETK-0016 Drop Python 3.10 so the lock can carry only patched Pillow

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
