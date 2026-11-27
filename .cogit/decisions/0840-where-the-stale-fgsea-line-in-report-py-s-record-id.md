---
template: adr
state: Proposed
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/fgsea-input, step: s2}
applies: [release-1-0-1/fgsea-input]
issue: 202
---

# Where the stale fgsea line in report.py's record_id docstring is fixed

## Background

Every detk command writes a module record whose id, and so its file name,
is a hash of what identifies the run (`record_id` in de_toolkit/report.py,
#182). Its docstring gives an example of a file a module does not record:
"fgsea's results file is in its command line only". release-1-0-1/fgsea-input
(#199, PR #200) makes fgsea record its results file in `in_file_paths`, so
after it merges that example is false. Only the docstring is stale; the code
and the published docs (docs/report.md, updated by #200) are right.

## Context

- fgsea-input's scope is de_toolkit/enrich.py, tests/enrich/, tests/report/
  and +CHANGELOG; report.py is outside it, so its developer left the line.
- No open node owns report.py. run-identity, which wrote the line, is done;
  lineage-test, the node the developer suggested, is scoped to tests/report/
  only. Any fix therefore widens some node's scope by one file.
- Criteria: the merged tree should not contradict itself; the widening should
  be the smallest and sit with the change that made the line stale.

## Options

**A. Widen fgsea-input to the one docstring line in report.py** (recommended).
The node whose change makes it stale fixes it in the same PR, so 1.0.1 never
carries a contradiction; one comment line, no behaviour, no test effect.
The fix, e.g.: "Runs that differ in any file, including one a module
records only in its command line, keep separate records".

**B. Widen lineage-test to the same line.** Same edit, later, in a node about
a test; the stale line lives in main between the two merges and lineage-test
gains a code file unrelated to its objective.

**C. Leave it** until a node next owns report.py. Cheapest now; a misleading
comment in the code that defines record identity, which an agent reading the
code would take as current.

## Decision

Proposed, for Adam: **A**. It keeps the fix with its cause, is the smallest
widening, and leaves lineage-test a pure test node. Not accepted by the
reviewer; PR #200 is approved without it, and A is a one-line follow-up
commit on node/199-fgsea-input if accepted.

## Consequences

- If A: fgsea-input's scope gains de_toolkit/report.py (docstring only); the
  developer adds one commit to PR #200 before s3.
- If B: lineage-test's scope gains de_toolkit/report.py.
- If C: the line stays stale in 1.0.1.
