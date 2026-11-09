---
kind: step
time: 2026-11-09T19:33:45Z
by: DETK/reviewer
node: release/fpkm
step: s2
branch: node/50-fpkm
verdict: approve
commits: []
decisions: []
---


# Review of PR #51: correct the FPKM formula (release/fpkm s2)

## Summary

`FPKMCounts` now computes `count / (length/1e3) / (library_size/1e6)`, i.e.
`count * 1e9 / (length * library size)` with library size the column total,
as DETK-0006 Option A requires. Lengths go through `_lengths_for`, the same
path `tpm` uses, so missing, zero, negative, NA, empty and non-numeric
lengths, features missing from the lengths file, duplicated IDs and numeric
IDs all behave identically to `tpm` (checked from the CLI, below). Row order
follows the counts file; an all-zero sample gives a NaN column and a
warning; the report's `length_quantiles` now summarize only the lengths
actually used. `test_fpkm` asserts hand-worked values, and the docs page and
the CHANGELOG "Changed" entry describe the correction. All acceptance
criteria are met. The findings below are all low severity and do not block.

Hand-worked example (counts rows in order z, x, y; lengths file with header
`id length`, rows x 500, y 1500, z 3000, plus an unused row):

| gene | len | s1 | s2 | s3 |
|------|-----|----|----|----|
| z | 3000 | 60 | 15 | 0 |
| x | 500 | 10 | 5 | 0 |
| y | 1500 | 30 | 0 | 0 |

Library sizes are s1 = 100, s2 = 20 and s3 = 0.
- s1: z 60e9/(3000*100) = 200,000; x 10e9/(500*100) = 200,000; y 30e9/(1500*100) = 200,000
- s2: z 15e9/(3000*20) = 250,000; x 5e9/(500*20) = 500,000; y 0
- s3: NaN (warning "some samples have zero total counts, their FPKM values are NaN")

`uv run detk-norm fpkm` printed exactly these values (to floating point), in
the counts-file row order z, x, y. With numeric IDs 201/101 (lengths 3000/500),
s1 = [60, 10] (library 70) gives 285,714.29 for both, which matches 60e9/(3000*70) and
10e9/(500*70).

## Artifacts

- Branch `node/50-fpkm` at 7d0cc3e; diff against origin/main: CHANGELOG,
  de_toolkit/norm.py, docs/tools/norm.md, tests/norm/test_norm.py, plus
  .cogit journal/plan files. Nothing is outside scope.
- `uv sync` ok; `uv run pytest`: 184 passed, 49 skipped; `ruff check`: pass;
  `ruff format --check`: pass; `mkdocs build --strict` (to a scratch dir): pass.
- `gh pr checks 51`: all pass (CodeQL, docs, ruff, tests 3.10-3.13) except
  "test with R (bioconda)", which was still pending when checked. FPKM does
  not touch R.
- CLI refusals, fpkm vs tpm: length 0, -5, NA, empty, `abc` each give the same
  error ("1 features have a length that is not a positive number ... y")
  and exit 1; missing feature, same "not found" error; duplicate ID in the
  file, same "lists 1 feature names more than once" error.
- `--report-dir`: the JSON for module `fpkmcounts` has `num_kept: 3` and
  `length_quantiles` running from 500 to 3000 (the unused length 9 is excluded),
  and it serializes. The HTML report was written.

## Findings

1. CHANGELOG:23 (low): the "Changed" line says "`detk-norm fpkm` output
   values change from 0.9.x". The bullet just above it (CHANGELOG:19-22)
   says the `fpkm` CLI failed on every run in 0.9.x, and DETK-0006 notes
   that the wrong numbers reached users only through the Python function
   `de_toolkit.norm.fpkm()`. The users this affects are those calling
   `fpkm()` (or `FPKMCounts`). Suggest naming the function as well, e.g.
   "`fpkm` (`detk-norm fpkm` and `de_toolkit.norm.fpkm()`)".
2. tests/norm/test_norm.py:461 (low): for `fpkm`, `test_all_zero_sample`
   checks only that the zero column is NaN and the warning appears. It does
   not check that the other columns still hold correct values (the CPM/TPM
   sum-to-1e6 check is skipped). The values are covered elsewhere, so this is
   a small gap.
3. tests/norm/test_norm.py:237 (low): `test_fpkm_nonpositive_lens`
   parametrizes 0, -5 and NaN but not a non-numeric string length in an
   in-memory Series (e.g. `"abc"`). `_lengths_for` coerces it and the CLI
   refuses it (verified), but there is no fpkm test for it. tpm's test has
   the same gap.
4. tests/norm/test_norm.py:520 (nit): `test_cpm_tpm_report_specs_compile`
   does not include `fpkmcounts`. It is exercised in
   tests/report/test_report_render.py:362 with synthetic properties, so this
   is not a gap in practice.

## Questions

- FPKM now depends on library size, but `FPKMCounts.properties` does not
  record `library_sizes` as `CPMCounts` does. Should the FPKM report show
  them? This is outside this node's acceptance, so it could be a follow-up.
- Out of scope, seen in passing: the run wrote `ro-crate-metadata.json` to
  the working directory rather than to `--report-dir`, and the report JSON
  says `detk_version: 0.9.12`. Both predate this PR.
