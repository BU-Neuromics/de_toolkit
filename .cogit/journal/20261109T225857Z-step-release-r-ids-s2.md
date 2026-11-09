---
kind: step
time: 2026-11-09T22:58:57Z
by: DETK/reviewer
node: release/r-ids
step: s2
branch: node/67-r-ids
verdict: changes
commits: []
decisions: []
---


# Re-review of #68: IDs as written through R, fgsea and tidy (head 3b89c7f)

## Summary

The code is unchanged since 55f96bd, and it still does what DETK-0015 option 2 asks. Both acceptance criteria are met. Commit 3b89c7f fixes the three earlier requests:

- The skill's ID paragraph now says that only the R-backed commands stop on a duplicate ID, and that the Python commands do not check. I confirmed this by hand.
- The CHANGELOG full stop is in place.
- The CHANGELOG now mentions the non-blind rlog fix.

I am asking for one more change, and it is a one-line fix. The new CHANGELOG entry says "`detk-transform rlog` with a design (not blind) works". The command cannot do that. The CLI passes `--blind False` as the string `"False"`, and Python treats that as true. So the command never sends the design or the column data to R (finding 1). The fix is reachable only from the Python API, `de_toolkit.transform.rlog(count_obj, blind=False)` or `RlogCounts`. Either say that in the entry, or fix `--blind` in the CLI, which would be outside this node's scope. Everything else is approve-level.

R evidence: `git diff 55f96bd 3b89c7f` touches only `.cogit/`, `CHANGELOG` and `skills/detk/SKILL.md`. No file under `de_toolkit/` or `tests/` changed. On 55f96bd, CI's "test with R (bioconda)" job 129486971589 succeeded with 412 passed and 5 skipped. Its checkout was the merge of 55f96bd into 194bd2a, which is the current origin/main. Its progress dots match the local collection order:

- `tests/de/test_de.py ............ss..`: positions 13 and 14 (`s`) are `test_firth_w_big/huge_data_cov`, and positions 15 and 16 (`.`) are `test_deseq2_keeps_padded_ids` and `test_firth_keeps_padded_ids`.
- `tests/transform/test_transform.py ...........`: positions 9 to 11 are the vst, rlog and non-blind rlog padded-ID tests, all `.`.
- `tests/wrapr/test_wrapr.py .........`: `test_wrapr_keeps_ids_as_written` is last and passes.

The R job on 3b89c7f has since succeeded, with the same counts and the same dots (see Artifacts).

## Artifacts

- Worktree at 3b89c7f, the same as origin/node/67-r-ids. origin/main is 194bd2a, which is also the merge base. `git merge-tree` is clean, and GitHub reports MERGEABLE.
- `uv sync`: OK.
- `uv run pytest`: 362 passed, 55 skipped (R-gated; R is not installed here).
- `ruff check .`: passed. `ruff format --check .`: exit 0.
- `mkdocs build --strict`: exit 0.
- `pytest tests/skills`: 19 passed.
- `gh pr checks 68`: CodeQL, docs, ruff and tests on Python 3.11, 3.12 and 3.13 all pass. "test with R (bioconda)" on 3b89c7f (job 129494715470, merge d2893ad of 3b89c7f into 194bd2a) succeeded with 412 passed and 5 skipped. The dots are identical: `test_de.py ............ss..`, `test_transform.py ...........`, `test_wrapr.py .........`. So all six R-gated padded-ID tests passed on the current head.
- Hand runs, with `001`-`004` sample names and IDs `007`, `010`, `1.10` and `1.1`:
  - `detk-filter`, `detk-norm cpm`, `detk-util tidy-counts` and `tidy-covs` keep every ID and sample name.
  - On origin/main, `tidy-counts` exits 1 on the same input ("all row IDs in the column data file exist as columns"). That matches the CHANGELOG's "where they used to exit 1".
- Duplicate `007`:
  - `detk-filter`, `detk-norm cpm`, `detk-transform plog` and `detk-util tidy-counts` write both rows.
  - `detk-stats summary` crashes with an AttributeError, which also happens on main.
  - So the skill's "the Python commands do not check" holds.
- The R side, with the R bridge stubbed (a fake `Rscript` on PATH, and `wrapr` patched to record its arguments):
  - `detk-de deseq2` and `detk-transform vst` hand the duplicate `007` rows to R unchanged.
  - In R they hit `rownames(cnts) <- cnts[[1]]` (de.py:258, 459) or `read.id.csv(..., row.names=TRUE)` (`rownames(df) <- ids`, wrapr.py:192). Both stop on duplicate row names, so the skill's "The R-backed commands stop" holds.
- The same stub, on `detk-transform rlog --blind False counts.csv counts~group cov.csv` (the sample-info file is supplied):
  - The call records `params={'design': '~ 1', 'blind': 'False'}` and `metadata=None`.
  - So the design is never fitted (finding 1).
- `read_result_stat` keeps `007` (twice) and `1.10`, and turns `NA` into NaN. `--statcol` pointing at a text column fails with pandas' raw parse message, as the earlier review noted.
- `read_id_table` keeps `" 007"` with its space, as the CHANGELOG says.

## Findings

1. **CHANGELOG:46-49, medium.** The entry "`detk-transform rlog` with a design (not blind) works ... it now drops both, as `detk-de deseq2` does" names the CLI command, but the CLI cannot take the non-blind path.
   - In `de_toolkit/transform.py:362-366`, docopt gives `--blind` as the string `"False"`.
   - `RlogCounts` tests `not blind` (transform.py:281, 289), and `not "False"` is false. The command therefore sends design `~ 1` and no column data, whatever design and sample-info file the user gives. I reproduced this with R stubbed.
   - A user reading the entry would run `detk-transform rlog --blind False` with a design and believe it was used.
   - Fix: reword the entry to the Python API (`de_toolkit.transform.rlog(count_obj, blind=False)`). The CLI `--blind` bug is the earlier review's finding 8, which is outside this node and suggested as an issue.
2. **skills/detk/SKILL.md:85-91, nit.** The new sentence is accurate, but it splits commands into "R-backed" and "Python". `detk-enrich fgsea` is R-backed and takes a result file, not a counts file, so it is in neither group. The pre-existing line 278 ("fgsea refuses an ID that appears twice") covers it.
   - Not introduced here: depending on the version, fgsea may only warn about duplicate names, not refuse them, although `enrich.py:230` assumes it rejects them. I could not check this without R.
   - No change needed for this node.
3. **Carried over from the earlier review, unchanged and not blocking:**
   - enrich.py:368 and 409: `--statcol` with a negative index is now refused, and naming a text column gives pandas' raw message.
   - util.py:813-845: tidy-covs drops the index name, adds a `counts` column and re-types padded covariates. This is pre-existing.
   - norm.py:183 and 209-210: plain `read.csv` remains there, but no CLI command reaches it. `detk-norm deseq2` uses the Python `DESeq2Norm`.
   - transform.py:362-366: the `--blind` string bug (see finding 1).

## Questions

- For finding 1, should the CHANGELOG be limited to the Python API (my recommendation, within scope), or should `--blind` be fixed in this PR? Fixing it would widen the node's scope and is the human's call.
- The follow-up issues the earlier review suggested (tidy-covs output quirks, rlog `--blind` parsing) are still open questions. If an issue is filed for `--blind`, it should mention that the CHANGELOG entry will become true for the CLI once it is fixed.
