---
kind: step
time: 2026-11-27T20:55:00Z
by: DETK/developer
node: release-1-0-1/fgsea-input
step: s1
branch: node/199-fgsea-input
verdict: done
commits: [0148e86]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Reproduction test (tests/enrich: test_fgsea_crate_lists_results_file_as_input) fails on v1.0.0 with KeyError in_file_paths; the crate action's object there is ../gene_sets.gmt plus the params. Fix: enrich.py passes in_file_paths=[gmt_fn, result_fn]; in_file_path stays the GMT. Docs (docs/tools/enrich.md, docs/report.md), record-identity test comments, CHANGELOG 1.0.1 Fixed entry. Note: report.py record_id docstring still says fgsea's results file is in its command line only; report.py is outside this node's scope, left as is.

## Artifacts

## Findings

## Questions
