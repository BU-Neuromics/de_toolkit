---
kind: task
objective: 'norm: detk-norm fpkm computes FPKM as documented, dividing by length in kb and library size in millions (DETK-0006)'
acceptance:
  - fpkm output equals count * 1e9 / (length * library size), and test_fpkm asserts the documented values
  - fpkm refuses missing, zero and negative lengths as tpm does (review of release/tpm-cpm, PR #40)
  - the CHANGELOG notes the correction of 0.9.x output under Changed
from: [DETK-0006]
scope: [de_toolkit/norm.py, tests/norm/, docs/tools/norm.md, +CHANGELOG]
prev: [release/tpm-cpm]
issue: 50
visited: a2140bc
---

# Correct the FPKM formula

## Implementation plan

- [x] @developer Fix the formula, the test and the CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes
