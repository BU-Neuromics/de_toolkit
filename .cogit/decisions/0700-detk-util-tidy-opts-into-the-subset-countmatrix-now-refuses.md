---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/sample-match, step: s1}
applies: [release-1-0-1/sample-match]
issue: 191
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27: Option A, CountMatrix subset=False keyword, Tidy passes subset=True; de_toolkit/util.py added to release-1-0-1/sample-match's scope as a bare entry"}
---

# detk-util tidy opts into the subset CountMatrix now refuses

- Proposed by: the developer session for release-1-0-1/sample-match (#178),
  2026-11-27, for the driver to confirm

## Background

DETK-0600 makes `CountMatrix` (de_toolkit/common.py), the shared matching
behind every command that reads a counts file and a sample information
file, refuse sample sets that differ. `detk-util tidy`, `tidy-counts` and
`tidy-covs` (the `Tidy` module in de_toolkit/util.py) are the explicit way
to subset the two files, and they do their matching by calling
`CountMatrix(counts, column_data)`, relying on the intersection it took in
1.0.0. With the check in `CountMatrix`, tidy would refuse exactly the case
it exists for. The node's scope is de_toolkit/common.py, tests/, docs and
the CHANGELOG; de_toolkit/util.py is not in it.

## Context

- Acceptance puts the check "in the shared matching (CountMatrix)" and
  names `detk-util tidy` as the way to subset, so both must hold.
- `CountMatrix` is in the public Python API (`de_toolkit.CountMatrix`,
  docs/api.md); a Python caller who passed mismatched frames got the same
  silent subset as the commands.
- tests/util/test_tidy.py pins tidy's subsetting (a sheet missing P1 and
  with an extra X9); it must keep passing unchanged.

## Options

**A. A `subset=False` keyword on `CountMatrix`; Tidy passes
`subset=True`** (recommended). The check is in `CountMatrix`, on by
default for every caller, CLI and Python; the subset is an explicit
opt-in, which is what DETK-0600 asks of the user too. Costs a one-line
change in de_toolkit/util.py, outside the node's listed scope.

**B. The check in `CountMatrixFile` only.** Every command builds its
matrix through `CountMatrixFile` (make_cli_count_obj, detk-wrapr run), and
Tidy uses `CountMatrix`, so util.py is untouched. But a Python caller of
`CountMatrix` keeps the silent subset, and the check sits in the file
reader rather than the shared matching that acceptance names.

**C. Tidy does its own intersection without `CountMatrix`.** Also edits
util.py, more lines than A, and duplicates the matching.

## Decision

Recommended: **A**. It keeps the check where acceptance puts it and closes
the silent subset for Python callers as well, at the cost of one line
outside the listed scope that only preserves tidy's existing behaviour.
The PR for #178 implements A; if the driver prefers B, the util.py line
reverts and the check moves to `CountMatrixFile`.

## Consequences

- `CountMatrix` gains a keyword (`subset`, default False); the CHANGELOG
  1.0.1 entry names it. No command line, output or JSON changes for tidy.
- tests/cli/test_sample_match.py pins the opt-in; tests/util/test_tidy.py
  is unchanged and passes.
- Revisit if another caller inside detk needs the subset.
