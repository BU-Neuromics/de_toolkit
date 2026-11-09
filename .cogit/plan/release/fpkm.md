---
kind: task
objective: 'norm: detk-norm fpkm computes FPKM as documented, dividing by length in kb and library size in millions (DETK-0006)'
acceptance:
  - fpkm output equals count * 1e9 / (length * library size), and test_fpkm asserts the documented values
  - 'fpkm refuses missing, zero and negative lengths as tpm does (review of release/tpm-cpm, PR #40)'
  - the CHANGELOG notes the correction of 0.9.x output under Changed
from: [DETK-0006]
scope: [de_toolkit/norm.py, tests/norm/, docs/tools/norm.md, +CHANGELOG]
prev: [release/tpm-cpm]
issue: 50
visited: a2140bc
status: done
done: 4f47522
---

# Correct the FPKM formula

## Implementation plan

- [x] @developer Fix the formula, the test and the CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Review of PR #51 (approve, 2026-11-09), minor findings noted rather than
fixed, on Adam's word: `test_all_zero_sample` checks only the NaN column
for `fpkm`, not the other columns' values; `test_fpkm_nonpositive_lens`
has no non-numeric length in an in-memory Series (the CLI refuses it;
`tpm`'s test has the same gap); `test_cpm_tpm_report_specs_compile` leaves
out `fpkmcounts` (covered in tests/report). The CHANGELOG finding was
folded in. Open question: should the FPKM report record `library_sizes`,
as CPM's does?
