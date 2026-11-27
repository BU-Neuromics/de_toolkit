---
kind: task
objective: a shared count-matrix check, wired into detk-norm cpm first, rejects duplicate sample headers (seen before pandas renames them A.1), duplicate feature IDs, negative counts and zero-depth samples, naming the offender
acceptance:
  - 'reproduced first as tests, each exiting 0 on v1.0.0 with the output shown: duplicate header ''gene,A,A,B'' (output columns A, A.1, B); duplicate feature g1 (two g1 rows normalized); a count of -1 (a negative CPM); sample A all zero (a blank column). After: each exits with the status DETK-0601 settles, no output file, and one stderr line naming the header, feature, sample and value at fault'
  - the check is one function in de_toolkit/common.py that the other readers can call (release-1-0-1/count-checks-readers); docs/tools/norm.md and CHANGELOG 1.0.1 say what cpm rejects
from: [DETK-0601]
scope: [de_toolkit/common.py, de_toolkit/norm.py, tests/norm/, tests/common/, +docs/tools/norm.md, +CHANGELOG]
---

# detk-norm cpm rejects malformed counts

## Implementation plan

## Notes
