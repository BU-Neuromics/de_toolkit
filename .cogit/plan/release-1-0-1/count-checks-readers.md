---
kind: task
objective: 'the count-matrix check of count-checks runs in every command that reads a counts matrix: duplicate sample headers and feature IDs everywhere; negative counts and zero-depth samples in the commands that need raw counts'
acceptance:
  - 'reproduced first: a test per command shows 1.0.0 accepting a duplicated sample header (renamed A.1) and a duplicated feature ID, and after, each exits as DETK-0601 settles, naming the offender'
  - negative counts and zero-depth samples are rejected where the command needs raw counts (detk-norm deseq2, library, tpm, fpkm; detk-de deseq2; detk-transform vst and rlog), and accepted where a matrix may be transformed (detk-stats, detk-filter, detk-outlier); the split is listed in docs/concepts.md and CHANGELOG 1.0.1
from: [DETK-0601]
scope: [de_toolkit/norm.py, de_toolkit/de.py, de_toolkit/transform.py, de_toolkit/stats.py, de_toolkit/filter.py, de_toolkit/outlier.py, tests/, +docs/concepts.md, +CHANGELOG]
---

# Every command that reads counts runs the count checks

## Implementation plan

## Notes
