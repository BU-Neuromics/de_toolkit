---
kind: task
objective: 'the count-matrix check of count-checks runs in every command that reads a counts matrix: duplicate sample headers and feature IDs everywhere; negative counts and zero-depth samples in the commands that need raw counts'
acceptance:
  - 'reproduced first: a test per command shows 1.0.0 accepting a duplicated sample header (renamed A.1) and a duplicated feature ID, and after, each exits 1 (DETK-0601), naming the offender'
  - negative counts and zero-depth samples are rejected where the command needs raw counts (detk-norm deseq2, library, tpm, fpkm; detk-de deseq2; detk-transform vst and rlog), and accepted where a matrix may be transformed (detk-stats, detk-filter, detk-outlier); the split is listed in docs/concepts.md and CHANGELOG 1.0.1
from: [DETK-0601]
scope: [de_toolkit/norm.py, de_toolkit/de.py, de_toolkit/transform.py, de_toolkit/stats.py, de_toolkit/filter.py, de_toolkit/outlier.py, tests/, +docs/concepts.md, +CHANGELOG]
prev: [release-1-0-1/count-checks]
issue: 201
visited: 29305c6
---

# Every command that reads counts runs the count checks

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

The second half of Adam's
item 2 ("count validation shared across readers, CPM first"). Which commands
take raw counts and which a transformed matrix is this node's call, listed
in the docs; the acceptance names the expected split.
