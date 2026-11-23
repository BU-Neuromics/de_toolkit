---
kind: step
time: 2026-11-23T17:54:38Z
by: DETK/developer
node: release/tidy-sheet-name
step: s1
branch: node/158-tidy-sheet-name
verdict: done
commits: [3092bbf]
decisions: []
---

# Done: Pass the sheet's name to _sniff in read_column_data; a FIFO test through detk-util tidy; CHANGELOG; open the PR

## Summary

read_column_data captures _source_name(f) before _rewindable and passes it to _sniff(name=); FIFO test through detk-util tidy (fails on main with <stream>, passes here); existing tidy tests unchanged; CHANGELOG under Fixed. ruff clean; full suite 2554 passed, 154 skipped.

## Artifacts

## Findings

## Questions
