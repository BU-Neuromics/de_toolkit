---
kind: step
time: 2026-11-21T02:36:43Z
by: DETK/developer
node: release/outlier-entropy
step: s1
branch: node/123-outlier-entropy
verdict: done
commits: [96f937e]
decisions: []
---

# Done: Replace the dropped_df.replace line and the positional relabel in EntropyCounts with a reindex by feature name; all-zero features get a missing entropy and a False flag with one warning; tests with all-zero features first, in the middle and last, each row checked against scipy.stats.entropy, through the API and the CLI; CHANGELOG; open the PR

## Summary

all-zero features missing and unflagged with one warning; rows on the input's index in its order; -p a fraction with exit 2 outside (0,1) (DETK-0200 Option A); tests through API and CLI; CHANGELOG; airway tutorial count 925; docs/example regeneration moved to release/example-paths; PR #125, CI green on 7f5f094 incl. R

## Artifacts

## Findings

## Questions
