---
kind: step
time: 2026-11-20T14:05:59Z
by: DETK/developer
node: release/cli-migrate
step: s3
branch: node/79-cli-migrate
verdict: done
commits: [520598c, 6c202f7, d4c6eea, 822612c]
decisions: [DETK-0070]
---

# Done: Migrate the other ten entry points with examples, harmonize metavars, fix the umbrella command, move the skill test to argparse (DETK-0010), regenerate the skill's usage blocks, remove docopt-ng and `test_docopt.py`, relock, CHANGELOG

## Summary

All 11 entry points on argparse with examples; metavars in one closed list (FILE/DIR/N + CHAR, COL, COLS, FMT, REGEX, WHAT, BOOL); DETK-0033 parse errors pinned; skill test on argparse (DETK-0070 supersedes DETK-0010, Provisional); usage blocks regenerated; docopt-ng and test_docopt.py removed, relocked after formula-migrate; CHANGELOG; s2 asks folded in; CI green incl. R

## Artifacts

## Findings

## Questions
