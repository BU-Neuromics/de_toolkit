---
kind: step
time: 2026-11-20T13:09:07Z
by: DETK/developer
node: release/formula-migrate
step: s1
branch: node/78-formula-migrate
verdict: done
commits: [89c3822]
decisions: []
---

# Done: Port `patsy_lite.py` to formulaic as studied in DETK-0024 (bool to categorical, float cast, backtick quoting, term order, error wrapping) and fix the DETK-0040 mismatches with their pins, keeping its parser, its `__` names and its API; rewrite the translation test; swap patsy for formulaic in `pyproject.toml`, relock; drop the patsy wording in `docs/formulas.md` and correct its two examples (DETK-0040); CHANGELOG; open the PR

## Summary

patsy-lite ported to formulaic; DETK-0040/0049 pins changed; docs and CHANGELOG; DETK-0080 accepted (Option A); PR #81

## Artifacts

## Findings

## Questions
