---
template: adr
state: Proposed
authority: [human]
date: 2026-11-20
from: {node: release/record, step: s1}
applies: [release/record]
issue: 107
---

# detk-de records its column data file in the module JSON, so the crate links it (de.py, outside release/record's scope)

- Proposed by: the release/record developer session, 2026-11-20 (step s1)

## Background

DETK-0061 item 5 (Accepted) says: "A later `detk-de` run that reads the
recorded output as column data then shows the recorded step as its
producer." The crate links a step to its inputs through the module JSON's
`in_file_path` and `column_data_path`. `detk-de` (deseq2, firth) passes
only `in_file_path` (the counts) to `DetkReport.add_module`; its
`column_data_path` is always null, although `<cov_fn>` is a required
positional of every detk-de subcommand. So the crate shows no link from
a column data file to the detk-de run that read it, recorded or not.
detk-filter and detk-stats already pass `column_data_path`.

release/record's R-gated test (`tests/util/test_record.py::
test_lineage_into_detk_de`) found it: it failed in the CI R job on PR
#106. `de_toolkit/de.py` is not in release/record's scope.

## Context

- The node's acceptance names "a detk step" for the lineage test, which
  the detk-filter test meets; the reviewer step (s2) and DETK-0061 name
  detk-de, the step a derived covariate is most often for.
- The change is additive: `column_data_path` is an existing envelope
  field (schema 1.0), null today for detk-de; no test pins it null for
  detk-de. Documents already written are unaffected; the module id does
  not hash it.

## Options

### Option A: release/record passes `column_data_path=args.cov_fn` in de.py (recommended)

One argument in one call; detk-de's crate actions gain the column data as
an `object`, so lineage into detk-de works for any producer (a recorded
step, detk-util tidy-covs where it records, a later detk command).

### Option B: drop the detk-de lineage test; a separate node fixes de.py

release/record meets its acceptance with detk-filter, but DETK-0061's
stated outcome stays untrue for detk-de until another node lands.

## Decision

Recommended: Option A. It is the one line that makes DETK-0061 item 5
true, it is additive to the envelope, and the R-gated test pins it. The
node's PR branch carries it.

## Consequences

`de_toolkit/de.py` (the report call) joins release/record's scope; the
CHANGELOG entry in s3 mentions that detk-de's module JSON now names its
column data file.
