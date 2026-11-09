---
kind: step
time: 2026-11-09T23:09:57Z
by: DETK/reviewer
node: release/r-ids
step: s2
branch: node/67-r-ids
verdict: changes
commits: []
decisions: []
---


# Third review of #68: IDs as written through R, fgsea and tidy (head 3553149)

## Summary

The code has not changed since 55f96bd: `git diff 55f96bd 3553149` touches only `.cogit/`, `CHANGELOG` and `skills/detk/SKILL.md`. It still does what DETK-0015 option 2 asks, and both acceptance criteria are met. The R job on the current head passed, and all six R-gated padded-ID tests ran (see Artifacts).

The reworded rlog entry now correctly names the Python API, and its account of the old failure is accurate. I checked this by hand: the design was `counts ~ Intercept + category__case`, and after the drops it is ` ~ category__case`. The CI log from 542893b shows the `checkFullRank` "not full rank" error.

I am asking for one more change. The entry's last clause is still wrong. It says `detk-transform rlog --blind False` "reads `False` as text, which counts as blind". Python does take the blind path. But the text value `"False"` also goes to R as `params$blind`, where DESeq2's `rlog()` evaluates `blind | is.null(mcols(object)$dispFit)`. A character value fails there with "operations are possible only for numeric, logical or complex types". So the command does not run blind. It exits 1, and it does the same for `--blind True` or any other explicit `--blind` value. Only leaving `--blind` out gives a working (blind) rlog. This is a one-line wording fix (finding 1). I am not asking for `--blind` to be fixed.

## Artifacts

- The worktree is at 3553149, the same as origin/node/67-r-ids. Freshly fetched origin/main is 406f53f (#66 merged since the last review). `git merge-tree --write-tree origin/main HEAD` is clean, and GitHub reports MERGEABLE.
- `uv sync`: exit 0.
- `uv run pytest`: 362 passed, 55 skipped (R-gated; R is not installed here).
- `uv run ruff check .`: all checks passed. `uv run ruff format --check .`: exit 0.
- `uv run --group docs mkdocs build --strict -d .../scratchpad/r3-68/site`: exit 0.
- `uv run pytest tests/skills`: 19 passed.
- `gh pr checks 68`: CodeQL (3 analyses), docs build (strict), ruff and tests on Python 3.11, 3.12 and 3.13 all pass.
- "test with R (bioconda)" passed in 9m30s: job 129499975996, run 42716693363. It checked out 551c6e3, the merge of 3553149 into 406f53f, which is the current main. The result was 416 passed and 12 skipped. Log: `.../scratchpad/r3-68/r.log`.
  - `tests/de/test_de.py ............ss..`: the two `s` are `test_firth_w_big/huge_data_cov`. `test_deseq2_keeps_padded_ids` and `test_firth_keeps_padded_ids` (positions 15 and 16) pass.
  - `tests/transform/test_transform.py ...........`: 11 of 11 pass, including the vst, rlog and non-blind rlog padded-ID tests.
  - `tests/wrapr/test_wrapr.py .........`: 9 of 9 pass. `tests/enrich/test_enrich.py` (21) and `tests/util/test_util.py` (7) also pass with no skips.
  - The other 10 skips are all in `tests/report/test_report_render.py` and `test_report_view_text.py`, which came from #66, outside this PR.
- Design probe: `CountMatrixFile(..., design="counts ~ category[cont]")` gives `'counts ~ Intercept + category__case'` with `counts` and `Intercept` columns in `full_matrix`. After rlog's two drops it gives `' ~ category__case'`. This matches the CHANGELOG's "passed the counts and an intercept column".
- R semantics, checked with a scratch conda env that has r-base and jsonlite (no DESeq2):
  - `read_json(simplifyVector=TRUE)` of `{"blind":"False"}` gives a character value.
  - `if (blind)` takes it as FALSE.
  - `blind | is.null(NULL)` fails with "operations are possible only for numeric, logical or complex types".
  - DESeq2's `R/rlog.R` (thelovelab/DESeq2; the file was last changed in 2023, so this also covers CI's 1.50.2) runs `if (blind)` at line 129 and `if (blind | is.null(mcols(object)$dispFit))` at line 136.
- Hand runs with sample names `001`-`004` and IDs `007`, `1.10`, `1.1`, `007` (a duplicate):
  - `detk-filter` and `detk-util tidy-counts` keep every ID and sample name and write both `007` rows.
  - So the skill's "the Python commands do not check" holds.

## Findings

1. **CHANGELOG:49-51, low-medium.** "`detk-transform rlog --blind False` reads `False` as text, which counts as blind" is false.
   - detk takes the blind path (`"~ 1"`, no column data), but it also passes `blind: "False"` to R (transform.py:289).
   - DESeq2's `rlog(dds, blind="False")` then stops at `blind | is.null(...)` (rlog.R:136) on the character value.
   - The command therefore exits 1 with an R error for any explicit `--blind`, `True` included. It does not run a blind rlog.
   - Suggested wording: "The command line cannot reach it yet: `detk-transform rlog --blind` passes its value to R as text, where DESeq2 stops; leave `--blind` out for a blind rlog."
   - I confirmed the R behaviour with r-base and DESeq2's source, but I did not run DESeq2 itself.
2. **de_toolkit/transform.py:281-286, low, carried.** `rlog(count_obj, blind=False)` drops `counts` and `Intercept` from the caller's `count_obj.design_matrix`, so `count_obj.design` becomes `" ~ ..."` after the call. `DESeq2Counts` does the same, and the fix is correct. I note it only because the CHANGELOG now advertises this API.
3. **skills/detk/SKILL.md:85-91, no issue.** The ID paragraph is accurate:
   - `007` and `001` survive the commands named.
   - `1.10` and `1.1` stay distinct.
   - The R-backed commands stop on a duplicate ID (`rownames<-` in `read.id.csv`, and `rownames(cnts) <- cnts[[1]]` in de.py).
   - The Python commands pass a duplicate through.
4. **Carried, out of scope, not blocking:**
   - The `--blind` parsing itself (transform.py:362-366).
   - `--statcol` negative indexes (enrich.py:368).
   - The tidy-covs output quirks (util.py:813-845).
   - norm.py's internal `read.csv`.

## Questions

- Finding 1 is wording only. Should it be fixed in this PR (my recommendation: the entry exists to tell users what works) or carried to the follow-up `--blind` issue? If that issue is filed, it should note that any explicit `--blind` currently fails in R, not only `False`.
