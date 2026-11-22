---
kind: step
time: 2026-11-22T15:39:51Z
by: DETK/reviewer
node: release/report-paths
step: s2
branch: review/report-paths
verdict: changes
commits: []
decisions: [DETK-0281]
---

# Changes asked: Review the PR: in one directory run two detk commands with --report-dir a and --report-dir b, read both crates and grep both reports and crates for the directory's absolute path and $HOME; run the quantifiers tutorial; check the crate with rocrate-validator

## Summary

Changes asked: absolute paths typed on the command line still reach argv, record's params/properties and the crate's parameter values, while the docs and CHANGELOG say no absolute path is recorded (DETK-0281 Proposed, recommend B); add a test with typed absolute paths that asserts no machine path. The crate placement, two report dirs, clean, relative @ids, profile conformance at REQUIRED, the tutorial and CI (R included) check out.

## Artifacts

## Findings

/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-rev-report-paths/b9e02854-1268-48cc-86a9-94b6e48d889c/scratchpad/findings.md

## Questions

- DETK-0281 Absolute paths typed into argv and params in module JSON and the crate (#137)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
