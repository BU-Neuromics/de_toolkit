---
kind: task
objective: on request (DETK-0604) the module JSON and crate record a SHA-256 of each input and output file of a native detk step
acceptance:
  - 'reproduced first as a test: no File entity in a v1.0.0 crate carries a checksum. After: requested as DETK-0604 settles, each File the step read or wrote has its sha256; not requested, the output is as in 1.0'
  - docs/report.md and CHANGELOG 1.1
from: [DETK-0604]
scope: [de_toolkit/report.py, de_toolkit/crate.py, tests/report/, +docs/report.md, +CHANGELOG]
---

# Optional checksums of each step's files

## Implementation plan

## Notes
