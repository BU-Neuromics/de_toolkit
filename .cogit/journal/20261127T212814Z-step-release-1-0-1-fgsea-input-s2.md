---
kind: step
time: 2026-11-27T21:28:14Z
by: DETK/reviewer
node: release-1-0-1/fgsea-input
step: s2
branch: review/fgsea-input
verdict: approve
commits: []
decisions: [DETK-0840]
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: the reproduction fails on v1.0.0 and passes here, both acceptance criteria hold, CI green at ee37e9e including the R job

## Artifacts

## Findings

Reproduction: tests/enrich/test_enrich.py::test_fgsea_crate_lists_results_file_as_input, copied into a v1.0.0 worktree (66628a8) and run against v1.0.0's de_toolkit (import path checked), fails with KeyError 'in_file_paths'; with that assert removed it fails on the crate, whose action's file objects are {../gene_sets.gmt} only, as the acceptance states. Here it passes.
Acceptance 1: enrich.py passes in_file_paths=[gmt_fn, result_fn] beside in_file_path=gmt_fn; the module JSON keeps in_file_path == gene_sets.gmt and lists both in in_file_paths; crate.py reads in_file_paths before in_file_path, so the action's object holds both files plus the params, ../de.csv a File entity, result ../enrich.csv. Same field and pattern as util.py's tidy and record; no schema change (1.1 field).
Acceptance 2: CHANGELOG 1.0.1 Fixed entry, citing DETK-0720 and #199.
Tests: tests/enrich and tests/report locally 234 passed, 27 skipped (R-gated). CI at ee37e9e all green, including 'test with R (bioconda)': 2783 passed, 23 skipped, none of them in test_record_identity.py, so the R-gated two-results-file test (which now also checks in_file_paths) ran and passed.
Scope: code and tests within enrich.py, tests/enrich/, tests/report/, CHANGELOG. docs/tools/enrich.md and docs/report.md are outside the listed scope paths but the step names docs and both edits are needed (docs/report.md's fgsea parenthetical would otherwise be false); accepted as in scope of the step.
Record ids: fgsea record ids change because the id hashes every recorded path (#182); expected, and each detk version changes ids anyway. Re-running fgsea into an existing 1.0.0 report directory leaves the old record beside the new one, as any version bump does.
Stale docstring: report.py record_id still says fgsea's results file is in its command line only. lineage-test cannot fix it without widening its scope (tests/report/ only), and no open node owns report.py; recorded DETK-0840 (Proposed, for Adam) recommending option A: fix it here as one docstring line, widening this node's scope by report.py. Not a blocker for approval.

## Questions

- DETK-0840 Where the stale fgsea line in report.py's record_id docstring is fixed (#202)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
