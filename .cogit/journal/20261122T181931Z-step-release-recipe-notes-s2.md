---
kind: step
time: 2026-11-22T18:19:31Z
by: DETK/reviewer
node: release/recipe-notes
step: s2
branch: review/recipe-notes
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: run the failing recipe on the page through detk-util record and read its last line, run each recipe on a header-only sheet, and read the skill's covariates reference as an agent would

## Summary

Approved: all three acceptance items hold. record's failure line shows a multi-line Miller program as '...' on one line (the page's failing recipe, run through record, ends '... '\''...'\'' sample_info_bad.csv (--verbose for the traceback)'), and _command_line is used only for messages; the recorded command stays shlex.join. On a header-only sheet all eight recipes exit 1 with no output and no module JSON. z-score and min-max print '<col> has no values: the sheet has no samples', and the others stop on record's missing-output message. The zero-padded note (010/05 typed as string, 05.5 as float, mlr -O reads 010 as 8), the constant-recipe rule and the stddev figure (1.066e-7 on Miller 6.22) were checked by hand, and the skill reference reads clearly for an agent. Full pytest gives 2551 passed and 101 skipped, and CI on ae19e19 is all green, including 'test with R (bioconda)'. Nits only.

## Artifacts

## Findings

1. Nit, not blocking: docs/recipes/covariates.md, the stddev paragraph (about line 308): the edited line "(1.07e-7 on Miller 6.22), not 0. For the same reason a column that does not vary is found by its" runs well past the page's wrap width. Cosmetic.
2. Note, not blocking: on a header-only sheet the z-score and min-max recipes print their own message, then Miller's "is_null type-assertion failed at NR=0" line, then record's line. That's the same three-line shape as every other recipe failure, and the acceptance asks only that Miller's "did not evaluate to boolean" is gone. It is.
3. Environment, not this PR: a fresh unpinned `roc-validator` (0.14.0) fails test_crate_validates_with_a_recorded_step ("does not reference the required context https://w3id.org/ro/crate/1.3/context"). uv.lock pins 0.11.3, which passes, so CI is unaffected. Worth knowing before 1.0 if roc-validator is ever unpinned.

## Questions
