---
kind: step
time: 2026-11-27T20:18:46Z
by: DETK/reviewer
node: release-1-0-1/run-identity
step: s2
branch: review/run-identity
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: reproduction fails on v1.0.0 (filter: one record naming b.csv, reproduced by hand too; 7/10 non-R identity tests fail there) and passes here; R CI job ran all 12 identity tests incl. deseq2 and fgsea; identical command keeps one record; docs/report.md and CHANGELOG 1.0.1; all changes in scope

## Artifacts

## Findings

Verified: (1) Reproduction: tests/report/test_record_identity.py copied onto a v1.0.0 worktree fails 7 of 10 non-R tests, including test_filter_runs_writing_different_outputs_keep_two_records (len(docs)==1); by hand on v1.0.0, detk-filter -o a.csv then -o b.csv leaves one json naming b.csv only. The deseq2/fgsea reproductions are R-gated, so not run locally on v1.0.0; the plan session reproduced them on main at 75aacb3. (2) On this branch tests/report passes locally (218 passed, 14 skipped). CI run 46059178701 at bb2889f is all green, and in 'test with R (bioconda)' test_record_identity.py ran 12/12 with none skipped (2766 passed, 23 skipped). 399b4d2 changes only .cogit/plan/release-1-0-1/run-identity.md. (3) Each acceptance criterion holds: two records each for filter, deseq2 and fgsea, all in the crate (the crate's object/result pairs are asserted for filter and deseq2; the action count for fgsea); an identical re-run replaces its one record; 'What identifies a record' in docs/report.md; CHANGELOG 1.0.1 entry. (4) Scope: report.py, tests/report/, docs/report.md, CHANGELOG, module_schema.json (description only, widened by the driver), plus .cogit records. (5) The trade-off of hashing argv: the same run typed differently (-o vs --output, an extra -v) gets its own record, which leaves a stale duplicate naming the same output. I accept it. v1.0.0 already left stale records when params changed with the same -o, so this is not a new kind of cost. It is the only in-scope way to keep fgsea runs apart until release-1-0-1/fgsea-input lands, and DETK-0720's Consequences settle it. Separating two different runs matters more than avoiding a duplicate. Before merge: the PR is CONFLICTING with main (CHANGELOG, where main's #187 added its own 1.0.1 'Fixed' entry, and .cogit/plan/release-1-0-1.md), so CI has not run tests on 399b4d2 (CodeQL only). Merge main, keep both 1.0.1 bullets under one heading, and wait for CI, R job included, to go green again before merging. Nits (not blocking): the docs line 'an absolute path and its relative spelling give the same id' holds, but ./counts.csv and counts.csv in argv give different ids, so 'its relative spelling' could say 'relative to workdir'. After merging main, the R-gating in test_record_identity.py could use #187's tests/r_packages.py helper instead of wrapr.check_r_package, for consistency.

## Questions
