---
kind: step
time: 2026-11-20T20:43:55Z
by: DETK/reviewer
node: release/parse-errors
step: s2
branch: review/parse-errors
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: try 3, 2.5 and -2.5 on each side of ~, cond[Z] and a misspelled term on the command line, and read each message as a user would

## Summary

Approved at d1621b4: DETK-0190 Option A holds for 3, 2.5, -2.5 on both sides of ~, with and without such a column; 0/1 keep their intercept meaning; cond[Z] in detk-filter exits 2 naming column, group and values with no output; misspelled terms give one plain line listing the columns; CI green incl. the R job on d1621b4; the test_r_design.py edit is a required consequence of DETK-0190. Two non-blocking notes.

## Artifacts

## Findings

Approve. Each acceptance item checked on the command line at d1621b4, with column data that has columns 3, 2.5, -2.5 and with one that does not.

- Number-like terms (DETK-0190 Option A): `counts ~ 3|2.5|-2.5` (deseq2) and `3|2.5| -2.5 ~ counts`, `c ~ counts + -2.5`, `c ~ counts - 2.5` (firth) each exit 2 naming the term. With such a column the message says to rename it to start with a letter or underscore (Miller's rename); without, it says only 0 and 1 have a meaning. `-2.5` is no longer dropped silently on either side. `1e3` is caught too; `.5` is an illegal-character error (not silent). `counts ~ 0 + c`, `counts ~ 1`, `counts ~ c - 1` build their designs and go on to the run. `counts ~ 1[a]` is a clear error.
- detk-filter: `mean(cond[Z]) > 1` exits 2: "the filter expression names the group 'Z' of the column 'cond', which has no such value (its values: A, B)"; no out.csv written; the duplicated warning is gone. `flag[1]`, `flag[1.0]`, `dose[0.5]`, `dose[.5]`, `b[true]` select their samples; `flag[2]`, `b[yes]`, `cond[1]` are usage errors listing the values. Tests in tests/filter/test_filter_groups.py and the cli-pin Line row cover it.
- Invalid designs: `counts ~ nope` / `counts ~ cnod` give "cnod in the design is not a column of the column data file (its columns: c, cond)"; `counts ~ cond[Z]` names the reference level and the values present. One line, no tuple text, no ANSI codes, no traceback. formulaic_message strips ANSI and the ⧛⧚ markers; tests/formula/test_formula_errors.py asserts plain one-line text for each wrapping path.
- tests/de/test_r_design.py (outside the node's scope): the edit is right. Both changed tests asserted that `2.5` / `1.0` resolve as columns, which DETK-0190 removes; they now assert the rename error. test_firth_number_shaped_column correctly drops @logistf_test because it fails before R runs; it passes locally without R. Nothing else in the file changed.
- CI on d1621b4: all 12 checks green, including 'test with R (bioconda)' (2264 passed, 21 skipped; tests/de/test_r_design.py 46/46 passed) and docs build (strict). Locally: 2196 passed, 89 skipped (R-gated). Merges cleanly with origin/main (118283e).
- docs/formulas.md states the rule and the plain-message behaviour; CHANGELOG has the DETK-0190 entry under Changed and the two fixes under Fixed, accurate to the behaviour.

Non-blocking notes (no change asked on this PR):

1. The CLI prefixes every design error with "Invalid design, detk formula syntax could not parse it: " (de_toolkit/common.py:655, outside scope). For "nope in the design is not a column ..." or a reference level the column lacks, the formula parsed fine, so "could not parse it" misleads slightly. Suggest a follow-up making it "Invalid design: ...".
2. Pre-existing: detk-filter prints "Generating LALR tables / WARNING: 4 shift/reduce conflicts" on stderr on every run (yacc tables built in a temp dir); same on main at 09ef1fd, unchanged by this PR. Also pre-existing: a design starting with `-` (`-2.5 ~ counts`) is taken by argparse as an option unless written with a leading space; not this node's.

## Questions
