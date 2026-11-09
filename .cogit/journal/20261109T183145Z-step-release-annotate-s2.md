---
kind: step
time: 2026-11-09T18:31:45Z
by: DETK/reviewer
node: release/annotate
step: s2
branch: node/29-annotate
verdict: changes
commits: []
decisions: []
---


# Review of PR #41: detk-util annotate, changes requested for numeric ID columns

## Summary

The join is sound for the main case: string IDs such as Ensembl, with or
without `--strip-versions`. Every result row is kept, in order, including
duplicate IDs. IDs with several mapping rows collapse to their distinct values
joined with `;`. Unmapped IDs get empty columns, or the row is dropped with
`--drop-unmapped`. Clashing columns get the suffix `_annot`. The delimiter is
sniffed (tab, comma and `;` all worked), and a mapping file that has only a
header works. The report view escapes the user strings it puts in its HTML
note. The docs and the CHANGELOG are accurate. All checks pass.

One problem blocks approval. The result table is read with inferred dtypes
(`util.py:254`), so a numeric ID column is not handled as text. Entrez-keyed
results are common, and with them:

- a missing ID makes the run crash with no output;
- IDs with leading zeros never match, and the output rewrites them.

The fix is small: read the ID column as `str` (or the whole result with
`dtype=str` for the key), and add a test for it.

The decisions DETK-0007 and DETK-0008 are sound and stay Provisional for the
human. DETK-0008 fixes `;` and `_annot` as part of the 1.0 output format, so
it deserves a deliberate acceptance at s3.

## Artifacts

- `uv sync`: ok
- `uv run pytest`: 159 passed, 49 skipped (R not installed locally), 1 warning (from rdflib)
- `uv run ruff check .`: all checks passed
- `uv run ruff format --check .`: 110 files already formatted
- `uv run --group docs mkdocs build --strict`: built with no warnings (only the mkdocs-material 2.0 notice)
- `gh pr checks 41`: ruff and test on Python 3.10 to 3.13 pass; "test with R (bioconda)" was still pending when checked
- Hand-made CLI runs, all through `uv run detk-util annotate --no-report`:
  - duplicate result IDs with `--strip-versions`: rows, order and versioned IDs kept; `2;3` for the multi-mapped ID
  - `--drop-unmapped --map-to=symbol,3`: names and positions mixed correctly
  - mapping with only a header: everything unmapped, no crash
  - zero-byte mapping: exits 1 with "Could not determine delimiter"
  - `-i gene` where `gene` is not the first column
  - Entrez IDs: integers, with `NA`, and with leading zeros
  - a mapping column named like the result's ID column: became `gene_id_annot`
  - a `;`-delimited mapping file

## Findings

1. **Numeric IDs in the result break the join** (`de_toolkit/util.py:254`,
   `:190`, `:214`). Severity: major. The mapping file is read with
   `dtype=str`, but the result file is not, so a numeric ID column is parsed
   as a number:
   - A result keyed by Entrez IDs with one missing value (`1, NA, 3`) becomes
     float. With pandas 3.0.5, `astype(str)` keeps the NaN, nothing matches
     ("features mapped: 0 of 3"), and the run then crashes with
     `sequence item 1: expected str instance, float found` when the warning
     joins `unmapped_examples` (`:234`). The run exits 1 and writes no output.
   - IDs with leading zeros (`007`) are parsed as `7`. They never match the
     mapping's `007`, and the output writes the ID as `7`. That breaks the
     promise in the docs that the result keeps "their original IDs".

   Integer Entrez IDs without gaps do work. Entrez-keyed results are common
   (limma/edgeR users, and GMT files keyed by Entrez), so this is the main
   path for many users, not an edge case. Fix: read the result with the ID
   column as `str` (resolving `--idcol` first, or reading with `dtype=str` and
   restoring the other columns' dtypes), drop or flag NaN keys explicitly, and
   add tests for a numeric ID column with a gap and with leading zeros.

2. **A mapping row with an empty value counts as mapped**
   (`de_toolkit/util.py:204`). Severity: minor. `mapped` means "the key is in
   the mapping", so `ENSG3` with an empty symbol and an Entrez ID counts as
   mapped. With `--map-to=symbol` that row is "mapped" but its symbol is
   empty, and `--drop-unmapped` keeps it. The decision is defensible, but the
   docs and the report label "mapped" do not say so. Either document it or
   count as mapped only rows where at least one added column is non-empty.

3. **The unmapped counts and examples are per row, not per distinct ID**
   (`de_toolkit/util.py:214`, `:222`). Severity: minor. With duplicate result
   IDs the warning reads "e.g. ENSG2.1, ENSG2.1, ENSG9.1".
   `num_unmapped`/`num_mapped` count rows, which matches "features in" and is
   fine. The examples should be de-duplicated, though: `.unique()` or
   `drop_duplicates()` before `.head(10)`.

4. **`-i` on a column other than the first moves the columns around**
   (`de_toolkit/util.py:208`). Severity: minor. With
   `-i gene` on `idx,gene,lfc`, the output is `gene,idx,lfc,...`: the join
   column becomes the index, and the old first column becomes a data column.
   No rows or values are lost, but the docs say the result "keeps its rows,
   their order and their original IDs", which a reader may take to include
   the column layout. Worth a sentence in the docs, or keeping the result's
   original index column as the index.

5. **The mapping file is not an RO-Crate input** (`de_toolkit/util.py`
   `_annotate_main`, `de_toolkit/crate.py`). Severity: minor, and already
   disclosed. The module JSON's params record `mapping_fn`, but the crate does
   not list the mapping file as an input object, and it is half of the run's
   provenance. DETK-0007 says so and defers it because `crate.py` is outside
   the node's scope. That is acceptable for this PR, but it should become a
   tracked follow-up rather than only a consequence in the record.

6. **One file outside the node's scope: `de_toolkit/crate.py:64`**. Severity:
   none (justified). It adds one entry to the `SUBTOOLS` table so the crate
   labels the module `detk-util annotate` instead of the fallback
   `detk annotate`. It is a mechanical registry line, which the s1 result
   discloses. The `.cogit/` files in the diff are cogit's own records.

7. **A note on the report, not caused by this PR** (`de_toolkit/templates/report.html:102`,
   `de_toolkit/report.py:289`). Severity: minor. The view's note is escaped
   correctly (`report_specs.py:353`), and the "Show data" view uses
   `textContent`. But the module JSON is embedded with
   `{{ modules_json|safe }}` inside `<script type="application/json">`, and
   `json.dumps` does not escape `</`. A feature ID such as
   `</script><script>...` in `unmapped_examples` would therefore end the
   script block. This bug was already there, but annotate is a new path for
   arbitrary strings from user files into the report. It belongs to a
   separate issue, not this PR.

8. **Tests** (`tests/util/test_annotate.py`). Severity: minor. The 11 tests
   cover the documented behaviours, but none covers duplicate result IDs
   (which work), numeric or NaN IDs (finding 1), or a mapping with only a
   header. Please add at least the numeric-ID tests with the fix.

## Questions

- DETK-0008 makes `;` and `_annot` part of the 1.0 output format, which
  DETK-0001 promises as stable. The choice is good, but it is a promise about
  the public surface. Should the human accept it explicitly at s3 rather than
  let it ride in with the PR?
- `--strip-versions` strips `\.\d+$` from any ID, so it also strips RefSeq
  versions such as `NM_000546.6`, which seems intended. Ensembl PAR IDs
  (`ENSG….5_PAR_Y`) are left alone and will not match their unversioned
  form. Is that acceptable for 1.0, or worth a sentence in the docs?
- Should a follow-up issue be opened for listing the mapping file as an
  RO-Crate input (finding 5)?
