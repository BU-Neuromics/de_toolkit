---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/crate-inputs, step: s1}
applies: [release-1-0-1/crate-inputs]
allowed_by: [reasonable]
issue: 212
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Accepted as recommended (A) under Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27."}
---

# Which crate-inputs gaps outside its scope this node closes

## Background

detk writes a Process Run Crate (`ro-crate-metadata.json`) in each report:
every detk command is an action whose `object` lists the files it read and
whose `result` the files it wrote. release-1-0-1/crate-inputs (#209, tracks
#45) makes every command list every file it read or wrote. Its scope is
util.py, filter/stats/transform/outlier/norm.py, crate.py, tests/report/
and the CHANGELOG, and PR for s1 fixes annotate, gather, rlog, vst/rlog
`--rda`, outlier entropy `--plot-output`, norm deseq2 `--size-factors` and
norm fpkm/tpm's lengths file. Reading the code for the PR found three
places outside that scope where the same gap or a now-stale statement
remains.

## Context

1. `detk-de deseq2` and `detk-de firth` `--rda FILE` write an RDS file that
   their crate action does not list (de_toolkit/de.py). `--routput-dir DIR`
   is a debugging directory, not a result, and is left out in any option.
2. `detk-enrich fgsea --rda FILE` writes an RDS file its action does not
   list (de_toolkit/enrich.py; fgsea-input, merged, recorded its results
   file only).
3. docs/report.md's module-JSON table says `in_file_paths` and
   `out_file_paths` are "written by `detk-util record`" and that "their
   first entries are also `in_file_path` and `out_file_path`". After
   fgsea-input and this node, annotate, gather, fgsea, norm, transform and
   outlier write them too; and gather keeps `in_file_path` empty (as in
   1.0.0, which tests/util/test_gather.py pins) while listing its files, so
   "first entries" does not hold for gather.

Criteria: the node's objective says "every file a command read or wrote";
1.0.1 should not ship a doc that contradicts the code; scope widening should
be the smallest that does it and stay with the change that causes it.

## Options

**A. Widen this node by de.py, enrich.py, docs/report.md and
tests/util/test_gather.py** (recommended). Same pattern as the PR: pass
`out_file_paths=[output, rda]` when `--rda` is given (with a reproduction
test each in tests/report/test_crate_inputs.py, faked like the vst/rlog ones
so no R is needed), reword the docs row to "a step with several files
(detk-util record and the commands that read or write a second file)", and
make gather's `in_file_path` its first file so the "first entries" rule
holds (one assertion in tests/util/test_gather.py). About 30 lines; the
objective is then met for every command.

**B. A, without the gather change**: keep gather's empty `in_file_path`
and say in docs/report.md that gather has no primary input. Smaller; the
documented rule gains an exception.

**C. Leave all three to a follow-up node.** This PR stays in scope; 1.0.1
ships with `--rda` of detk-de and fgsea missing from the crate and a stale
docs row, unless the follow-up lands before the cut.

## Decision

Proposed, for Adam: **A**. It finishes the node's objective in the PR that
states it, with the same mechanism and test pattern, and leaves no
documented rule with an exception. Not applied: the PR for s1 stays within
the listed scope until this is answered.

## Consequences

- If A or B: crate-inputs' scope gains de_toolkit/de.py, de_toolkit/enrich.py,
  docs/report.md (and for A tests/util/test_gather.py); the developer adds
  one commit to the PR before review.
- If C: a follow-up node (e.g. release-1-0-1/crate-rda) owns the three.
