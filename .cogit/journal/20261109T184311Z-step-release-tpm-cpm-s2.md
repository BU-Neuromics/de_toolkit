---
kind: step
time: 2026-11-09T18:43:11Z
by: DETK/reviewer
node: release/tpm-cpm
step: s2
branch: node/24-tpm-cpm
verdict: approve
commits: []
decisions: []
---


# Re-review of PR #40: detk-norm cpm and tpm

## Summary

All five findings of the earlier s2 review are fixed, and the fixes are
tested. Numeric feature IDs now work for `tpm` and `fpkm`. A duplicated ID
is refused, both in the lengths file and in an in-memory Series. A
headerless file whose first length is `NA` keeps that row, and `tpm` says
the length is "not a positive number". The all-zero sample is tested for
`cpm` and `tpm`. The lengths-file rules are in the CHANGELOG, the docs page,
the CLI help and DETK-0005.

The statistics are right. I checked them by hand on a 3x2 example with the
rows out of order (g3 = 0,4; g1 = 1,2; g2 = 3,4; lengths g1 1000, g2 2000,
g3 4000):

- CPM: the column totals are 4 and 10, so CPM is g3 0/400000, g1
  250000/200000, g2 750000/400000.
- TPM: the per-kb rates are a = 0, 1, 1.5 (sum 2.5) and b = 1, 2, 2 (sum 5),
  so TPM is g3 0/200000, g1 400000/400000, g2 600000/400000.

The CLI writes exactly these values and keeps the counts file's row order.
The FPKM arithmetic is unchanged (count / (1e6 * length)), as DETK-0006
requires. It is fixed later, in release/fpkm.

Two minor points remain. Neither blocks the merge. IDs with leading zeros
do not match (finding 1). `fpkm` still accepts NA, zero and negative lengths
without an error, and fix 3 adds one new way to reach that (finding 2).

## Artifacts

- PR BU-Neuromics/de_toolkit#40, branch node/24-tpm-cpm at 64bb17d, diffed
  against origin/main
- `uv run pytest`: 178 passed, 49 skipped (no R), 1 warning (the rdflib
  ConjunctiveGraph deprecation)
- `uv run ruff check .`: clean. `uv run ruff format --check .`: 115 files
  already formatted. `uv run --group docs mkdocs build --strict`: clean.
- `gh pr checks 40` at 64bb17d: CodeQL, docs build (strict), ruff, test on
  Python 3.10 to 3.13 and Analyze (actions, python) all pass. "test with R
  (bioconda)" was still pending when I recorded this.
- CLI runs (`uv run detk-norm ...`) on hand-made files:
  - `cpm`, `tpm`, `fpkm` and `library`, with the lengths file with and
    without a header: values as above, row order kept.
  - Numeric IDs 101/102/103, with the lengths in a different order: `tpm`
    and `fpkm` work, and the output keeps the 101..103 IDs.
  - A duplicated g1 in the lengths file: `tpm` and `fpkm` both exit 1 with
    "lists 1 feature names more than once ... g1".
  - A headerless file whose first length is NA: `tpm` exits 1 with "1
    features have a length that is not a positive number ... g1".
  - Lengths 0 and -5: `tpm` exits 1 and names both features.
  - An all-zero sample: `cpm` and `tpm` write an empty (NaN) column, and the
    other column sums to 1e6.
  - `--report-dir` with the all-zero sample: the HTML and the module JSON
    are written, and the JSON parses strictly (no NaN).
  - IDs with leading zeros (007/008): see finding 1.

## Findings

1. Minor. Leading zeros. de_toolkit/norm.py:357 (`keys =
   count_df.index.astype(str)`) and de_toolkit/common.py:306
   (`CountMatrixFile` reads the counts index with an inferred dtype).
   - What happens: with IDs `007` and `008` in both files, the counts
     reader turns them into the integers 7 and 8. `_align_lengths` then
     compares "7" with "007", and `tpm` exits 1 saying "2 indices ... not
     found in the lengths parameters: 7, 8". `cpm` (and every other tool)
     writes them as 7 and 8.
   - Why it matters: docs/tools/norm.md:81-82 says numeric IDs "match, and
     appear in the output as in the counts file". That is true for Entrez
     IDs but not for zero-padded ones.
   - Scope: the lossy step is the shared counts reader, which this node
     does not own and which affects all detk tools. Zero-padded numeric
     gene IDs are uncommon.
   - Suggested action: a follow-up issue on reading the counts index as
     text, or narrow the docs wording to "integer IDs such as Entrez gene
     IDs". This does not block the merge.
2. Minor. `fpkm` does not check that lengths are positive. de_toolkit/norm.py:308
   (`FPKMCounts` uses `_align_lengths`, not `_lengths_for`).
   - What happens: NA, 0 and -5 lengths give NaN, inf and negative FPKM
     values, with no error and exit 0. This was already true on main, and
     the docs say only `tpm` checks lengths (docs/tools/norm.md:110).
   - What the fixes changed: the new header rule keeps a first row whose
     length is NA. Before, `fpkm` dropped that row as a header and refused
     the file with "not found". Now it writes an empty row and exits 0.
   - Suggested action: having `fpkm` use `_lengths_for` would change its
     validation, not its arithmetic. The release/fpkm acceptance does not
     list it, so add it there, or do it here if Adam prefers.
3. Nit. de_toolkit/norm.py:319-325. `FPKMCounts.properties` repeats the
   body of the new `_length_quantiles` helper (norm.py:329), which
   `TPMCounts` uses. This is cleanup that could go with release/fpkm.
4. None. The out-of-scope `de_toolkit/crate.py` change (SUBTOOLS entries for
   `cpmcounts` and `tpmcounts`) is needed for RO-Crate provenance and was
   disclosed in s1. The `.cogit/` files are bookkeeping for this node.

Status of the earlier s2 findings:

- 1, numeric IDs: fixed. `_align_lengths` matches as text. Tested by
  `test_tpm_numeric_ids` and `test_norm_cli_numeric_ids[tpm|fpkm]`, and
  confirmed on the CLI.
- 2, duplicated IDs: fixed in `read_lengths` and for in-memory Series.
  Tested by `test_read_lengths_duplicate_ids` and
  `test_duplicate_lens_series`, and confirmed on the CLI.
- 3, header detection: fixed for `tpm`. Tested by
  `test_read_lengths_missing_first_length_is_not_header`, and confirmed on
  the CLI. For `fpkm`, see finding 2.
- 4, all-zero sample: tested by `test_all_zero_sample[cpm|tpm]`, and
  confirmed on the CLI.
- 5, out-of-scope files: still justified.
- The earlier CHANGELOG question is answered: the entry now states the
  lengths-file rules.

## Questions

- DETK-0005 is still Provisional under DETK/developer, and it was revised
  to put the lengths-file rules on the 1.0 surface. As asked in the earlier
  review: should Adam confirm it at s3?
- Should length validation for `fpkm` (finding 2) be added to release/fpkm's
  acceptance?
