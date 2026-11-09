---
kind: step
time: 2026-11-09T23:19:59Z
by: DETK/reviewer
node: release/r-ids
step: s2
branch: node/67-r-ids
verdict: approve
commits: []
decisions: []
---


# Fourth review of #68: IDs as written through R, fgsea and tidy (head bc9841b)

## Summary

bc9841b makes only the wording change the third review asked for. The rlog entry's last clause now reads "`detk-transform rlog --blind` passes its value to R as text, where DESeq2 stops; leave `--blind` out for a blind rlog". That is accurate. `git diff 55f96bd HEAD -- de_toolkit tests` is empty, so the code and the R-gated tests that the earlier reviews approved are unchanged. Every sentence of the #67 entry, the rlog entry and the skill's ID paragraph matches the code. The PR is ready for s3.

## Artifacts

- The worktree is at bc9841b, the same as origin/node/67-r-ids and the PR head. `git diff --stat 55f96bd HEAD` touches only `.cogit/`, `CHANGELOG` (12 lines) and `skills/detk/SKILL.md` (5 lines). `git diff 55f96bd HEAD -- de_toolkit tests` is empty.
- Freshly fetched origin/main is 406f53f. `git merge-tree --write-tree origin/main HEAD` exits 0 (clean), and GitHub reports MERGEABLE.
- `uv run pytest -q`: 362 passed, 55 skipped (R-gated; R is not installed locally).
- `uv run ruff check .`: all checks passed. `uv run ruff format --check .`: exit 0.
- `uv run --group docs mkdocs build --strict -d .../scratchpad/r4-68/site`: exit 0.
- `gh pr checks 68` on bc9841b: all 10 checks pass: CodeQL and Analyze (actions, javascript-typescript, python), docs build (strict), ruff, tests on Python 3.11, 3.12 and 3.13, and "test with R (bioconda)" (8m38s, job 129505315413, run 42718269283). The R job checked out 74db0f2, the merge of bc9841b into 406f53f, which is the current main. It ran 416 passed and 12 skipped, the same as on 3553149: `tests/de/test_de.py ............ss..` (the two skips are the firth big/huge data tests), `tests/transform/test_transform.py ...........` and `tests/wrapr/test_wrapr.py .........` all pass.
- R semantics, rechecked with the third reviewer's r-base and jsonlite env (`.../scratchpad/r3-68/renv`):
  - `read_json(simplifyVector=TRUE)` of `{"blind":"False"}` gives class `character`.
  - `if (blind)` takes it as FALSE.
  - `blind | is.null(NULL)` fails with "operations are possible only for numeric, logical or complex types".
  - `if ("N")` fails with "argument is not interpretable as logical".
  - DESeq2 itself was not run. For the source (`R/rlog.R`, where `if (blind)` is at line 129 and `if (blind | is.null(mcols(object)$dispFit))` is at line 136), I rely on the third review.

## Findings

1. **CHANGELOG:46-51, no issue (the third review's finding 1 is resolved).** I checked each part of the rlog entry against the code:
   - With column data, `rlog(count_obj, blind=False)` drops `counts` from the LHS and `Intercept` from the RHS (transform.py:281-286). This is the same as deseq2, and the "not full rank" account was verified in the earlier reviews.
   - "The command line cannot reach it yet" holds. docopt's `--blind N` gives a string, `not "False"` is false in Python, and so the non-blind path is never taken from the CLI.
   - "passes its value to R as text, where DESeq2 stops" also holds. `params["blind"]` is the string (transform.py:289), and the R script hands it unchanged to `rlog(dds, blind=blind)` (transform.py:268, 276). Before that point detk's script never evaluates `blind`, so the stop happens inside DESeq2's `rlog`.
     - `"False"` and `"True"` pass `if (blind)` and stop at `blind | ...`.
     - Any other text, such as `"N"`, stops already at `if (blind)`.
     - Either way the stop is in DESeq2, for any explicit value.
   - "leave `--blind` out for a blind rlog" holds. A missing `--blind` becomes Python `True` (transform.py:362-363), which reaches R as logical TRUE.
2. **CHANGELOG:27-45 (#67 entry), no issue.**
   - The full stop the first review asked for is now present ("...with the IDs as text. The IDs are kept exactly as written...").
   - The commands, the fgsea and tidy claims, `read.id.csv(fn, row.names=TRUE)` and the whitespace example match the code reviewed in the earlier rounds, which has not changed since.
3. **skills/detk/SKILL.md:85-91, no issue.** The ID paragraph is unchanged since the third review, which hand-verified it.
   - The R-backed commands stop on a duplicate ID.
   - The Python commands pass a duplicate through.
   - `007`, `001`, `1.10` and `1.1` survive.
4. **Carried, out of scope, not blocking:**
   - The `--blind` parsing (transform.py:362-366). A follow-up issue should say that any explicit `--blind` fails in R.
   - `rlog`/`DESeq2Counts` modify the caller's `design_matrix`.
   - `--statcol` negative indexes (enrich.py:368).
   - tidy-covs output quirks (util.py:813-845).
   - norm.py's internal `read.csv`.

## Questions

- None blocking. The `--blind` CLI bug still needs its own issue, if one has not been filed.
