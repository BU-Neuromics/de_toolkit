---
kind: task
objective: every command that matches a counts file to a sample information file exits 1 naming the samples found in only one of them, where 1.0.0 fitted the intersection silently; a pure reorder stays allowed (DETK-0600)
acceptance:
  - 'reproduced first as a test: counts with samples 001-008 and a sample sheet where 008 is replaced by 999 (the audit''s case); on v1.0.0 detk-de deseq2 ''counts ~ batch + condition'' exits 0, fits 7 samples and writes results with no warning. After: exit 1, no output file, stderr one line ''detk-de: error: ...'' naming 008 (counts only) and 999 (sample information only)'
  - the same samples in another order exit 0 with results equal to the ordered input's; --strict still requires the same order
  - the check is in the shared matching (CountMatrix), and a test pins it for each command that takes a sample information file (detk-de deseq2 and firth, detk-transform with a design, detk-filter, detk-stats, detk-outlier where they take one); the tutorials and docs examples still run
  - docs/concepts.md says the sample sets must match and detk-util tidy is the explicit way to subset; CHANGELOG 1.0.1 notes the behaviour change (DETK-0600)
from: [DETK-0600]
scope: [de_toolkit/common.py, +tests/, +docs/concepts.md, +CHANGELOG]
---

# Counts and sample information with different samples are an error

## Implementation plan

## Notes
