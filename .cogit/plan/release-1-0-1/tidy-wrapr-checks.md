---
kind: task
objective: detk-util tidy, tidy-counts, tidy-covs and detk-wrapr run apply the duplicate sample-header and feature-ID checks (check_counts with values=False, from count-checks-readers and DETK-0830/DETK-0850)
acceptance:
  - 'reproduced first: on main, ''detk-util tidy-counts'' given gene,A,A,B,C with column data naming A, B and C exits 0 and writes gene,A,B,C, silently dropping the second A; a test shows it. After: exit 1 (DETK-0601) and one stderr line naming the duplicate; the same for a duplicated feature ID, and for tidy, tidy-covs and detk-wrapr run'
  - negative counts and zero-depth samples are still accepted by these commands (values=False); docs/concepts.md's list of commands and checks and CHANGELOG 1.0.1 include them
from: [DETK-0850]
prev: [release-1-0-1/count-checks-readers]
scope: [de_toolkit/util.py, de_toolkit/wrapr.py, tests/, +docs/concepts.md, +CHANGELOG]
issue: 218
visited: bfbc2c1
---

# detk-util tidy and detk-wrapr run check sample headers and feature IDs

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Added on the driver's direction, 2026-11-27, from DETK-0850 (Accepted;
proposed by the @reviewer of count-checks-readers, PR #203, which lands the
record and `check_counts`). Reproduced by the plan session on main at
d1f1343: `detk-util tidy-counts dup.csv cov.csv` with `gene,A,A,B,C` and
column data A, B, C exits 0 and writes `gene,A,B,C` (the second A, read as
`A.1`, dropped). `_tidy_main` in util.py calls `read_id_table` directly and
wrapr.py's `CountMatrixFile(...)` passes no `check`. Waits on
count-checks-readers for the shared check and DETK-0850's file.

`from: [DETK-0850]` belongs in the header, but the record is only on PR
#203's branch and `cogit validate` refuses a reference to it on main; add
it when this node is visited, after #203 merges.
