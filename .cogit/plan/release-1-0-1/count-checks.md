---
kind: task
objective: a shared count-matrix check, wired into detk-norm cpm first, rejects duplicate sample headers (seen before pandas renames them A.1), duplicate feature IDs, negative counts and zero-depth samples, naming the offender
acceptance:
  - 'reproduced first as tests, each exiting 0 on v1.0.0 with the output shown: duplicate header ''gene,A,A,B'' (output columns A, A.1, B); duplicate feature g1 (two g1 rows normalized); a count of -1 (a negative CPM); sample A all zero (a blank column). After: each exits 1 (DETK-0601: a bad input file, as DETK-0031 says), no output file, and one stderr line naming the header, feature, sample and value at fault'
  - the check is one function in de_toolkit/common.py that the other readers can call (release-1-0-1/count-checks-readers); docs/tools/norm.md and CHANGELOG 1.0.1 say what cpm rejects
from: [DETK-0601]
prev: [DETK-0601]
scope: [de_toolkit/common.py, de_toolkit/norm.py, tests/norm/, tests/common/, +docs/tools/norm.md, +CHANGELOG]
---

# detk-norm cpm rejects malformed counts

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; each of the four reproduced with
`detk-norm cpm`, exit 0: 'gene,A,A,B' gives columns A, A.1, B; two g1 rows
both normalized; -1 gives a negative CPM; an all-zero sample gives an empty
column. The duplicate-header check must read the header line itself, since
pandas renames a repeated name to A.1 on read (de_toolkit/common.py, about
line 995). The exit status is 1 (DETK-0601, accepted 2026-11-27): Adam's direction first said exit 2;
DETK-0031 makes a bad input file 1. Collides with sample-match on
de_toolkit/common.py; land one, then rebase the other.
