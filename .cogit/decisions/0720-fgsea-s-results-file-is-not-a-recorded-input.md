---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/run-identity, step: s1}
applies: [release-1-0-1/run-identity]
allowed_by: [reasonable]
issue: 189
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Accepted under Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27. Resolved as: handled by the planned node release-1-0-1/fgsea-input (enrich.py lists the DE results file as an input, after fgsea-statcol); no new node."}
---

# fgsea's results file is not a recorded input

- Proposed by: the release-1-0-1/run-identity session (#182), 2026-11-27,
  for the driver to confirm

## Background

Every detk command writes a module record (`<report-dir>/json/<id>.json`)
naming the files it read and wrote; the report and the Process Run Crate
are built from those records, the crate listing each recorded input as an
action's `object`. `detk-enrich fgsea <gmt_fn> <result_fn>` records only
the GMT (`in_file_path=args.gmt_fn`, de_toolkit/enrich.py about line 520).
Its results file, the ranking it tested, appears nowhere in the record
except the command line (`argv`), and the crate does not list it as an
input. Its ranking options (`-i`, `-c`, `-a`, `--abs`) are not in its
`params` either.

## Context

- #182 (this node) makes runs that differ only in their files keep
  separate records. Its acceptance includes two fgsea runs differing only
  in the results file. Its scope is de_toolkit/report.py, tests/report/,
  docs/report.md and the CHANGELOG; de_toolkit/enrich.py is outside it.
- Within that scope the node hashes the recorded `argv` into the record id
  as well as every recorded path. That separates the two fgsea runs (and
  runs differing only in `-c`, the plan note's reproduction), and any other
  module whose files or options reach only its command line. It does not
  put the results file in the record's paths or in the crate.
- The crate is detk's standards-facing provenance; an action that does not
  name the file it ranked is incomplete provenance, though not a silent
  wrong answer.

## Options

**A. A follow-up node in 1.0.1 or 1.1** (recommended): fgsea passes
`in_file_paths=[gmt_fn, result_fn]` to `add_module` (schema 1.1's field,
as detk-util record does), so the record and the crate list both inputs;
optionally its ranking options join `params`. Small, in enrich.py and its
tests; no interface change beyond a fuller record.

**B. Widen #182 to include enrich.py.** Same change, done here; reaches
outside the node's scope, which is the human's call.

**C. Leave it.** The `argv` in the id keeps fgsea runs apart; the crate
stays without the results file.

## Decision

Recommended: **A**. #182's acceptance holds without it (the `argv` in the
id), and the crate gap is a separate, small provenance fix that belongs in
the module that knows its inputs.

## Consequences

- Under A, a new node scoped to de_toolkit/enrich.py and tests/enrich/;
  #182 is unchanged.
- Under any option, #182 keeps `argv` in the id: a command spelled
  differently (`-o` for `--output`, an extra `-v`) is a new record, the
  cost of never collapsing two different runs into one.
