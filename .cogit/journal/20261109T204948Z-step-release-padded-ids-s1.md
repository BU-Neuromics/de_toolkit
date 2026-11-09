---
kind: step
time: 2026-11-09T20:49:48Z
by: DETK/developer
node: release/padded-ids
step: s1
branch: node/48-padded-ids
verdict: done
commits: [349da2d, 1be15cb]
decisions: []
---

# Done: Fix it with tests and a CHANGELOG entry; open the PR

## Summary

The shared reader keeps IDs and sample names as written for every command that reads counts in Python (read_id_table, PR #56): regular files, .gz, FIFOs, /dev/stdin, URLs and ~ paths; three review rounds; the R-backed commands, fgsea and the tidy commands go to release/r-ids (DETK-0015, accepted, option 2).

## Artifacts

## Findings

## Questions
