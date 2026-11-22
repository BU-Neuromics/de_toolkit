---
kind: step
time: 2026-11-22T15:39:38Z
by: DETK/reviewer
node: release/outlier-entropy
step: s2
branch: review/outlier-entropy
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: run detk-outlier entropy on a counts file with an all-zero gene in the middle and check a few genes after it against their own entropies

## Summary

Changes asked: all-zero genes missing/unflagged and every row on its own feature (checked against scipy), -p a fraction with exit 2 outside (0,1), CHANGELOG, airway 925 and docs/example moved to release/example-paths all hold, CI green incl. R on 7f5f094; but the entropycounts report card draws the threshold at the fraction on the 0-99 percentile axis (x=0.05, not 5), and the PR conflicts with main (CHANGELOG) so CI has not run on c36f543

## Artifacts

## Findings

/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-rev-outlier-entropy/1c946e87-44e2-4cef-845e-84445fc4b7c4/scratchpad/findings.md

## Questions
