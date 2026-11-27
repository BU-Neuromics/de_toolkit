---
kind: step
time: 2026-11-27T20:29:46Z
by: DETK/reviewer
node: release-1-0-1/count-checks
step: s2
branch: review/count-checks
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: check_counts keeps each column's name as written through selection and reorder; cpm's four rejections hold; CI green at 75ceaa5 including R

## Artifacts

## Findings

Re-review at 75ceaa5 (fix 35dbe09 plus a merge of main d2e203d). The change asked in the first review is resolved: read_id_table now keeps a dict from the table's column name to its name as written, and check_counts looks up each of counts.columns in it, falling back to str(c). The requested tests are present and pass: negative-count and zero-depth messages after a subset and a reorder (['B','C'] and ['C','B']); a selection without the offender passes; a repeated name that survives the selection (['B','A.1','A']) and one that doesn't (['A','B'], ['A.1','B']); and an end-to-end CountMatrix with column data (counts[common_names]) naming sample B. Against main, the diff is still only common.py, norm.py, tests/common, tests/norm, docs/tools/norm.md and the CHANGELOG 1.0.1 entry; the merge kept #187's CHANGELOG entry beside this one. Local: 2658 passed, 155 skipped; ruff clean. CI at head 75ceaa5: all 12 checks pass, including 'test with R (bioconda)' and 'docs build (strict)'. The reproduction verdict from the first review stands (the tests fail on v1.0.0 code and pass here). Nit, non-blocking: after a reorder, the duplicate-header message's 'sample columns i and j' count positions in the table passed in, not in the file header (cpm never reorders, so cpm's message counts positions in the file); the docstring says positions are counted among the samples, which is consistent. The earlier nit (an all-missing sample reported as zero-depth) stands as non-blocking. No decision needed; none recorded.

## Questions
