---
template: adr
state: Proposed
authority: [human]
date: 2026-11-09
from: {node: release}
applies: [release]
issue: 22
---

# Leave the PCA_tester data in git history or rewrite it out before 1.0

- Proposed by: a coding session, from #22 (2026-08-11); recorded here 2026-11-09

## Background

Phase 1 removed `PCA_tester/` from the working tree, but its CSV is
still in git history and so in every clone. Rewriting history removes
it, at the price of new hashes for every later commit and a
force-push to `main`.

## Context

- History audit on #22: the pack is 28.7 MiB; `PCA_tester/all_salmon_norm.csv`
  is 47.9 MB uncompressed. No credentials were ever committed.
- The CSV holds normalized expression for human brain samples with
  coded IDs (BA9, C/H prefixes), likely the lab's published HD BA9
  cohort. Whether it is public and unrestricted is known only to Adam.
- The cost of a rewrite grows after the 1.0.0 tag, a DOI and forks.

## Options

### Option A: leave history alone

Zero disruption. Right if the data is published and unrestricted.

### Option B: rewrite before 1.0

`git filter-repo --path PCA_tester --invert-paths`, force-push, re-push
branches. Right if any data-use restriction applies.

## Decision

Recommendation (#22): A if the data is unrestricted, B at once if not.
The answer turns on the data's provenance, which is Adam's.

## Consequences

Under B, every commit hash after the touched commit changes, including
those this record and the plan cite; it must happen before the tag.
