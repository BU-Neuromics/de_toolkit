---
kind: task
objective: 'The RO-Crate provenance records every file a command read or wrote: annotate''s mapping file (tracks #45), gather''s inputs, sample information files and side outputs'
acceptance:
  - 'reproduced first as a test per command: on v1.0.0 the crate action lacks the file named; after, every file the command read or wrote is in its object or result'
  - 'annotate''s mapping file (#45), gather''s per-sample files, the sample information file of detk-filter, detk-stats, detk-transform and detk-outlier, and detk-norm deseq2 --size-factors'' file are recorded; CHANGELOG 1.0.1'
scope: [de_toolkit/util.py, de_toolkit/filter.py, de_toolkit/stats.py, de_toolkit/transform.py, de_toolkit/outlier.py, de_toolkit/norm.py, de_toolkit/crate.py, de_toolkit/de.py, de_toolkit/enrich.py, docs/report.md, tests/util/test_gather.py, tests/report/, +CHANGELOG]
prev: [release-1-0-1/fgsea-input, DETK-0890]
issue: 209
visited: c490c55
---

# Annotate's mapping file in the provenance

## Implementation plan

- [x] @developer Write the reproduction tests of the first acceptance criterion and confirm they fail on v1.0.0; then fix, with a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.

Moved from features into 1.0.1 on 2026-11-27 by the plan session: the audit's
provenance finding asks to "record every input and side output", which is
this node's bug (#45) widened. Read on main: annotate passes only the
results file (`mapping_fn` is a param); gather passes no input
(`params["files"]` instead); detk-filter, detk-stats, detk-transform and
detk-outlier pass the counts file but not a sample information file they
read (detk-de records it, DETK-0161); detk-norm deseq2 --size-factors does
not list the size-factors file it writes. fgsea's results file is
fgsea-input's. Acceptance widened to match:
- reproduced first as a test per command: on v1.0.0 the crate action lacks
  the file named; after, every file the command read or wrote is in its
  object or result
- annotate's mapping file (#45), gather's per-sample files, the sample
  information file of filter, stats, transform and outlier, and side
  outputs (norm --size-factors) are recorded; CHANGELOG 1.0.1
