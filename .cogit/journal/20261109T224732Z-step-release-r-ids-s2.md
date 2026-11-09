---
kind: step
time: 2026-11-09T22:47:32Z
by: DETK/reviewer
node: release/r-ids
step: s2
branch: node/67-r-ids
verdict: changes
commits: []
decisions: []
---


# Review of #68: IDs as written through R, fgsea and tidy

## Summary

The code does what DETK-0015 option 2 asks, and both acceptance criteria are met. deseq2, firth, vst and rlog read counts and metadata through `read.id.csv`: the first column is read as text, and the other columns are re-typed with `type.convert(as.is=TRUE)`. wrapr reads R's output back with `read_id_table`. fgsea reads the result IDs as text, and tidy-counts and tidy-covs compare sample names as text. No R script in de.py or transform.py still uses plain `read.csv`.

The non-blind rlog fix is correct. It drops `counts` from the LHS and `Intercept` from the RHS, as deseq2 does, and only a call that used to fail is affected.

I am asking for changes for one reason: the new SKILL.md sentence says a file listing the same ID twice "is refused". That is false for the Python commands (finding 1). Fixing it, and the CHANGELOG punctuation (finding 2), is a two-line change. Everything else is approve-level.

I did not run R here because it is not installed. The R behaviour comes from CI's "test with R (bioconda)" job logs. All six R-gated tests ran and passed there. Run 42711044257, on commit 542893b, failed `test_rlog_not_blind_keeps_padded_ids` with `checkFullRank`, which proves that test executes in R. Run 42712945201, on commit 55f96bd, reports 412 passed and 5 skipped, and the per-file progress dots place a `.` at every new test's position. The current head d22d8d2 differs from 55f96bd only in `.cogit/` files, and its R job was still pending when I wrote this.

## Artifacts

- Diff `origin/main...d22d8d2`, freshly fetched. It merges cleanly (`git merge-tree`), and GitHub reports it MERGEABLE.
- `uv sync` succeeded. `uv run pytest` gave 362 passed and 55 skipped (R-gated) on Python 3.13.
- `ruff check .` passed. `ruff format --check .` exited 0. `mkdocs build --strict` exited 0.
- `gh pr checks 68`: CodeQL, docs, ruff and tests on 3.11, 3.12 and 3.13 all pass. "test with R" is pending on d22d8d2 and succeeded on 55f96bd (code-identical).
- CI R log for job 129486971589:
  - `tests/de/test_de.py ............ss..`: the two `s` are `test_firth_w_big_data_cov` and `test_firth_w_huge_data_cov` at positions 13 and 14. Positions 15 and 16 are `test_deseq2_keeps_padded_ids` and `test_firth_keeps_padded_ids`, both `.`.
  - `tests/transform/test_transform.py ...........`: 11 of 11 pass, including the vst, rlog and rlog-not-blind tests at positions 9 to 11.
  - `tests/wrapr/test_wrapr.py .........`: 9 of 9 pass, with `test_wrapr_keeps_ids_as_written` last.
  - The 5 skips are the 2 above and 3 in `test_report_render.py`.
- Hand runs without R:
  - tidy-counts and tidy-covs with `001` to `004` and `007`, `010`, `1.10`, `1.1` keep every ID. They exit 1 when sample 004 is missing from the covariates.
  - `read_result_stat` keeps `007` and `1.10`; the default statistic is the last numeric column, and `--statcol` works by name or position.
  - The FGSEARes-patched CLI test passes.
  - Duplicate IDs with `detk-filter`, `detk-norm cpm` and `detk-stats summary` (see finding 1).
  - The same tidy-covs input against `origin/main` (see finding 6).

## Findings

1. **skills/detk/SKILL.md:89-90, medium.** "a file that lists the same ID twice is refused" is not true across detk.
   - A counts file with `007` twice passes through `detk-filter` and `detk-norm cpm` unchanged, and both rows are written.
   - `detk-stats summary` crashes with `AttributeError: 'DataFrame' object has no attribute 'tolist'`. That crash already happens on main.
   - Only the R-backed commands refuse duplicate IDs, through R's `duplicate 'row.names'` error in `read.id.csv` and in de.py's `rownames(cnts) <- cnts[[1]]`.

   An agent reading the skill would skip a duplicate check it still needs. Either limit the sentence to the R-backed commands or drop it.
2. **CHANGELOG:43, low.** "...to read the counts or metadata with the IDs as text" has no full stop, so it runs straight into "The IDs are kept exactly as written, including whitespace...". The old text ended "(DETK-0015)." here.
3. **de_toolkit/transform.py:282-286, low.** The non-blind rlog fix is correct and matches deseq2 (`de.py:224,227`, `norm.py:222-223`).
   - On main, `rlog(count_obj, blind=False)` with a design always failed with `checkFullRank`, as CI run 42711044257 shows. No working behaviour changes.
   - Like deseq2, it modifies the caller's `count_obj.design_matrix`: `count_obj.design` becomes `" ~ ..."`.
   - The CHANGELOG does not mention the fix. Consider adding it to the latent-bug-fixes line.
4. **de_toolkit/enrich.py:368, low.** The behaviour of `--statcol`/`--idcol` changed in two places.
   - A negative position such as `--statcol=-1` used to pick the last column through Python's negative indexing. It is now refused. The usage text only promises a 0-based index, so this is acceptable, but it is a change.
   - An explicit `--statcol` naming a non-numeric column now fails with pandas' raw "Unable to parse string" message (`enrich.py:409`). Before, it reached fgsea. The CLI catches the error and exits 1.
   - On the default path, a `True`/`False` column is no longer taken as the "last numeric column", where pandas' bool dtype used to qualify. That is an improvement.
5. **read.id.csv (de_toolkit/wrapr.py:179-195), no issue.**
   - The non-ID columns are typed as `read.csv` types them:
     - `type.convert(as.is=TRUE)` uses the same `na.strings="NA"`, `dec` and `numerals` defaults.
     - Blank fields become NA in numeric or logical columns and stay `""` in text columns, the same as before.
     - `TRUE`/`T` become logical.
     - With R 4.x defaults, nothing becomes a factor.
   - An all-digit covariate meant as a factor, such as batch `01`/`02`, still becomes integer 1 and 2, exactly as `read.csv` and pandas (`read_id_table`) type it. Only the first column is kept as text.
   - In deseq2 and firth the metadata R reads is the encoded `full_matrix`, so covariate typing hardly matters there.
   - An ID literally `NA` still becomes a missing row name and R stops, as before.
   - The row names are set with `rownames(df) <- ids`, so duplicate or missing IDs stop R.
6. **de_toolkit/util.py:813-845 (tidy-covs), low, not introduced here.** The output loses the index name (header `,group,batch,counts`), gains a `counts` column of zeros, and re-types a padded covariate value (`01` becomes `1`). The same input does the same on `origin/main` with `s1`-style names. That is outside this node, so I suggest an issue.
7. **de_toolkit/norm.py:183,209-210, low, outside scope.** `estimateSizeFactors_wrapr` and `deseq2_wrapr` still use `read.csv(row.names=1)`. Only the tests reach them, and no CLI command does, and DETK-0015 names only the four commands, so I note them for completeness.
8. **de_toolkit/transform.py:362-366, low, not introduced here.** `detk-transform rlog --blind False` passes the string `"False"`, which Python treats as true. The CLI therefore never takes the non-blind path with column data, and the design file is ignored. Only the Python API runs non-blind rlog, so the fix in finding 3 is reachable only from there. I suggest an issue.

## Questions

- Should the skill's duplicate-ID sentence be limited to the R-backed commands, or should duplicate refusal become a rule for every command (a new decision, outside this node)?
- Should the tidy-covs output quirks (finding 6) and the rlog `--blind` string bug (finding 8) become follow-up issues before 1.0?
- I took the R behaviour from CI logs and did not run it here. I am highly confident that all six R-gated tests ran and passed on 55f96bd: the positional dots match the collection order, the skips are elsewhere, and the earlier run failed one of them in R. The R job on d22d8d2 was still pending when I wrote this.
