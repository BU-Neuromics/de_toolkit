---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/count-checks-readers, step: s1}
applies: [release-1-0-1/count-checks-readers]
allowed_by: [reasonable]
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A. Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27"}
---

# Where the readers run the count checks

- Proposed by: the @developer session of release-1-0-1/count-checks-readers s1, 2026-11-27

## Background

release-1-0-1/count-checks (#196) added `check_counts` in
`de_toolkit/common.py`. It rejects a repeated sample header, a repeated
feature ID, a negative count and a zero-depth sample. Today only
`detk-norm cpm` calls it, on `count_obj.counts`, after `make_cli_count_obj`
has built the `CountMatrix`. This node has every other command that reads
counts run the check: the two duplicate checks everywhere, and the two
value checks only where the command needs raw counts. Its scope is the six
command modules (norm, de, transform, stats, filter, outlier), tests/, docs
and the CHANGELOG. `de_toolkit/common.py` is not in its scope.

## Context

- **The check is too late in the command modules.** `CountMatrix.__init__`
  keeps only the samples the column data names
  (`counts.columns.intersection(column_data.index)`). The design fit can
  also drop samples (`self.counts[full_matrix.index]`). A repeated header
  `A,A` is read as `A, A.1`. When the column data names only `A`, the
  `A.1` column is dropped silently before any command module sees the
  matrix. So a check in `de.py`, `stats.py` and the rest passes it. This
  is the first acceptance criterion's own case for `detk-de deseq2` and
  every other command given `--column-data`. I checked this on 29305c6:
  `gene,A,A,B,C` with column data `A,B,C` gives `CountMatrix.counts`
  columns `['A','B','C']`, and `check_counts` accepts it.
- **The split needs a switch the function lacks.** `check_counts` always
  runs all four checks. A command that may take a transformed matrix
  (stats, filter, outlier) needs only the two duplicate checks. Without a
  parameter, each command module would have to work around the function.
  One way is to call it on a copy whose values are all 1. Another is to
  copy its duplicate checks into each module. Both are worse than a
  keyword argument.
- **The two reviewer nits from #196 are in common.py too.** Nit 1: after a
  reorder, the duplicate-header message counts positions in the table, not
  in the file. Nit 2: a sample whose values are all missing or non-numeric
  is reported as having "no counts". Both live in `check_counts`.
- **A collision.** release-1-0-1/sample-match (#198, in progress) is also
  editing `CountMatrix` in common.py. A check placed in
  `make_cli_count_obj` or `CountMatrixFile`, before `CountMatrix`, does not
  touch the lines sample-match edits. Either way, this node would merge
  main after #198 lands.
- The 1.0 interface promise does not change under any option. Exit 1
  (DETK-0601) and the messages are those of #196.

## Options

**A. Widen the scope to `de_toolkit/common.py` and check at the read**
(recommended).
- Add a keyword to `check_counts`: `values=True`. With `values=False`, it
  runs only the header and feature-ID checks.
- `make_cli_count_obj(args, raw=...)` calls it on the table as read, after
  `read_id_table` and before `CountMatrix` selects or reorders any column.
  Each command module passes `raw=True` or `raw=False`. `outlier`'s direct
  `CountMatrixFile` call does the same, through a small helper in
  common.py.
- `cpm`'s post-hoc call in norm.py moves to the shared path.
- Fold in both nits. A duplicate at the read is counted in file order, so
  nit 1 goes away. A sample with no numeric values gets its own message,
  "has no numeric counts".
- Meets every acceptance criterion with one code path. The diff to
  common.py is small, about 20 lines.

**B. Stay in scope: call `check_counts` in each command module after
`make_cli_count_obj`.**
- Misses a duplicate whose renamed column the column data or the design
  drops. So acceptance 1 fails for `detk-de deseq2` and every command run
  with column data.
- The raw/transformed split needs the values-of-1 workaround or a copy of
  the duplicate checks in six modules.
- Neither nit can be folded in.

**C. Stay in scope: each command module reads the counts itself, checks,
then builds the `CountMatrix`.**
- Checks before the selection, but it copies `make_cli_count_obj` into six
  modules.
- The split still needs a workaround.
- It drifts from sample-match's changes to `CountMatrixFile` and
  `CountMatrix`.

## Decision

Recommended: **A**, widen release-1-0-1/count-checks-readers's scope by
`de_toolkit/common.py`. Limit it to `check_counts`, `make_cli_count_obj`
and `CountMatrixFile`, and leave `CountMatrix.__init__` alone. Only a check
on the table as read can meet the node's first acceptance criterion. B
fails it, and C meets it by copying the shared read into six modules.

## Consequences

- The node's scope gains `de_toolkit/common.py`, and its plan file records
  that.
- Collides with sample-match on common.py. The edits are in different
  functions, so merging main is expected to be routine.
- `check_counts` gains a keyword argument (`values=True` by default), so
  existing callers are unaffected. `make_cli_count_obj` gains `raw`. It
  defaults to running the duplicate checks only, so a command left
  unmarked still rejects a malformed header.
- If the driver prefers B, acceptance 1 should drop "each command" for the
  commands run with column data. Otherwise that case stays open.
