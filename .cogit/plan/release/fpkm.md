---
kind: task
objective: 'norm: detk-norm fpkm computes FPKM as documented, dividing by length in kb and library size in millions (DETK-0006)'
acceptance:
  - fpkm output equals count * 1e9 / (length * library size), and test_fpkm asserts the documented values
  - the CHANGELOG notes the correction of 0.9.x output under Changed
from: [DETK-0006]
scope: [de_toolkit/norm.py, tests/norm/, docs/tools/norm.md, +CHANGELOG]
prev: [release/tpm-cpm]
---

# Correct the FPKM formula

## Implementation plan

- [ ] @developer Fix the formula, the test and the CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes
