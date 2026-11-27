---
kind: step
time: 2026-11-27T19:55:33Z
by: DETK/reviewer
node: release-1-0-1/count-checks
step: s2
branch: review/count-checks
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Changes asked: cpm's four rejections hold and reproduce on v1.0.0, but check_counts names the wrong sample on a column subset or reorder, which the readers node will hit

## Artifacts

## Findings

Verified: tests/norm/test_cpm_count_checks.py fails on 61ada60 (v1.0.0 code: 5 failed, DID NOT RAISE SystemExit) and passes at a9d9dbd; by hand on v1.0.0 each of the four files exits 0 with A,A.1,B / two g1 rows / -250000.0 / a blank column, as the node says. At a9d9dbd each exits 1, writes no output or report, one stderr line naming the offender. Full suite 2642 passed, 154 skipped; ruff clean; CI all green including 'test with R (bioconda)' (19m45s) and docs build (strict). Diff is inside scope (common.py, norm.py, tests/norm, tests/common, docs/tools/norm.md, CHANGELOG 1.0.1).

CHANGE ASKED (blocking, acceptance 2: 'one function the other readers can call'): read_id_table stores the header as a positional list in attrs[COLUMNS_AS_WRITTEN], and pandas carries attrs through column selection, so after counts[cols] the list no longer lines up with counts.columns. check_counts then indexes columns[col] into the stale list. Reproduced: t = read_id_table('gene,A,B,C / g1,1,-2,3 / g2,0,5,6'); check_counts(t[['B','C']]) says "feature 'g1' in sample 'A' has a negative count, -2" (the sample is B); the zero-depth message is misnamed the same way. CountMatrix.__init__ does exactly this (counts = counts[common_names], common.py ~634) when column data is given, which is how the readers node (release-1-0-1/count-checks-readers) will call it. cpm takes no column data, so this PR's cpm is not affected today. A length check alone is not enough: a same-length reorder also misaligns. Suggested fix: keep a mapping from pandas' column name to the name as written (e.g. {'A':'A','A.1':'A','B':'B'}) and have check_counts look up each of counts.columns in it (falling back to str(c) for a name not in it), so selection and reorder stay right; add a unit test for t[['B','C']] and a reordered subset, and one where the duplicate survives selection (t[['A','A.1']] of 'gene,A,A,B') and one where it does not.

Nit (non-blocking): a sample whose values are all missing/non-numeric sums to 0 after coercion and is reported as 'has no counts: its counts sum to 0'; acceptable, but you may prefer to leave it to the readers node's non-numeric handling.

No decision needed; none recorded.

## Questions
