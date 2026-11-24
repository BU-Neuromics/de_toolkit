---
kind: step
time: 2026-11-24T04:49:25Z
by: DETK/developer
node: release/cut
step: s2
branch: node/168-cut
verdict: done
commits: [6a6f471, 2692208, b41a244, 62bc808, 2f63d94, 0d86114]
decisions: []
---

# Done: Bump `version.py` to 1.0.0, set `Development Status :: 5 - Production/Stable`, date the CHANGELOG heading, and read the 1.0 entries against the released CLI: the option-names entry (about line 109) still lists `detk-filter --column-data` and `detk-stats --column-data` among renamed metavars, which 1.0 removes (DETK-0030); drop them there, as the entry on their removal already says; open the PR

## Summary

Version-bump PR #169: version.py 1.0.0, Production/Stable, CHANGELOG dated 2026-11-23 with a Breaking changes from 0.9 list, stale --column-data metavar lines dropped, plus the audit fixes Adam approved (example regenerated for 1.0.0, skill, README, Dockerfile jsonlite, pyproject URLs/PEP 639/numpy>=2 pandas>=3, CI comment and -rs). CI green including R; approved by rev-cut at s8.

## Artifacts

## Findings

## Questions
