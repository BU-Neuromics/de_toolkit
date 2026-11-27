---
kind: task
objective: on request (DETK-0604) the module JSON and crate record a SHA-256 of each input and output file of a native detk step
acceptance:
  - 'reproduced first as a test: no File entity in a v1.0.0 crate carries a checksum. After: requested as DETK-0604 settles, each File the step read or wrote has its sha256; not requested, the output is as in 1.0'
  - docs/report.md and CHANGELOG 1.1
from: [DETK-0604]
scope: [de_toolkit/report.py, de_toolkit/crate.py, tests/report/, +docs/report.md, +CHANGELOG]
prev: [release-1-0-1/run-identity, release-1-0-1/crate-inputs]
---

# Optional checksums of each step's files

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.1 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.1.0; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.1 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the audit: "native detk file checksums are generally absent"
(confirmed: no sha256 in a 1.0.0 crate). Optional (Adam): how it is asked
for is DETK-0604.
