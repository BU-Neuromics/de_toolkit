---
kind: step
time: 2026-11-09T20:40:22Z
by: DETK/reviewer
node: release/padded-ids
step: s2
branch: node/48-padded-ids
verdict: approve
commits: []
decisions: []
---


# Third review of #56: read feature IDs as text in the shared reader

## Summary

The regression from the second review is fixed. `read_id_table` now
buffers only a local path that exists and is not a regular file. URLs,
`file://` paths and an unexpanded `~/` path go to pandas again, as on
`main`. I ran every input kind on `main` and on this branch:

- Every input that `main` reads, the branch also reads, and keeps `007`.
- A missing path and a directory raise the same errors as on `main`.

The new `~` test fails on b30c683 and passes on b7c844f. The fuzz gives
the same result as in both earlier reviews. The real commands keep `007`
and the padded sample names. All local checks pass.

The branch merges cleanly with the current `origin/main` (a8b1316, the
#46 report escaping). DETK-0015 matches the code apart from two loose
phrases, which are listed under Questions. The remaining findings are
info only. I approve.

## Artifacts

- Head b7c844f. Merge base 081b3e8. `origin/main` a8b1316 merges
  cleanly (`git merge-tree`); its only changes are to `report.py`, its
  tests and `.cogit`.
- Local checks:
  - `uv sync`: ok.
  - `uv run pytest`: 303 passed, 49 skipped.
  - `ruff check`: all checks passed.
  - `ruff format --check`: 182 files already formatted.
  - `mkdocs build --strict`: exit 0.
- `gh pr checks 56`: all 10 pass, including "test with R (bioconda)" (8m49s).
- Input kinds, through `CountMatrixFile(...).counts` on `c.csv` (`id,001,002,003` /
  `007` / `42` / `0099`). Script: r3-56/probe.py. `main` is the code of `origin/main`
  on `PYTHONPATH`.

  | input | main | branch |
  |---|---|---|
  | regular file (two parses on the path, checked with a spy) | ok, `[7, 42, 99]` | ok, `['007','42','0099']` |
  | `c.csv.gz` | ok, ints | ok, `007` |
  | FIFO `ff.csv` | ok, ints | ok, `007` |
  | FIFO `ff.csv.gz` | ok, ints | ok, `007` |
  | `<(zcat c.csv.gz)` | ok, ints | ok, `007` |
  | `cat c.csv \| ... /dev/stdin` | ok, ints | ok, `007` |
  | `/dev/stdin < c.csv` | ok, ints | ok, `007` |
  | `http://127.0.0.1:8765/c.csv` (`python3 -m http.server`) | ok, ints | ok, `007` |
  | `http://.../c.csv.gz` | ok, ints | ok, `007` |
  | `file:///.../c.csv` | ok, ints | ok, `007` |
  | `'~/c.csv'` (unexpanded, `HOME` set to the scratch dir) | ok, ints | ok, `007` |
  | missing `nope.csv` | FileNotFoundError | FileNotFoundError (same message) |
  | a directory | IsADirectoryError | IsADirectoryError |
  | `io.StringIO` | ok, ints | ok, `007` |
  | text handle `open(p)` | ok, ints | ok, `007` |
  | binary handle `open(p, "rb")` | ok, ints | ok, `007` |
  | `gzip.open(p, "rt")` | ok, ints | ok, `007` |
  | binary handle on `c.csv.gz` | ok, ints | ok, `007` |

  The sample columns are `001,002,003` on both, and the counts are
  int64 on both.
- `test_read_id_table_tilde_path_goes_to_pandas`:
  - Fails on b30c683, with `FileNotFoundError` at common.py:349.
  - Passes on b7c844f.
- Fuzz (rv56/fuzz.py, unchanged): ok 13221, fallback 321, mismatch 0,
  new-only errors 0. This is identical to both earlier reviews.
- Real commands on the branch (outputs in r3-56/):
  - `detk-norm deseq2 c.csv`: rows `007`, `42`, `0099`; header
    `001,002,003`.
  - `detk-norm tpm c.csv len.csv`: same rows. `len.csv` has `007` and
    `0099`, and they match.
  - `detk-norm cpm` on a mixed column (`007`, `ENSG1`): `007` kept.
  - `detk-filter 'mean(condition[test]) > 4' c.csv info2.csv` (sample
    names `001..003`): keeps `007` and `0099`. On `main` the same
    command fails with "No sample names were found to be in common".
  - `detk-stats summary`, `rowdist` and `pca`: `007` rows and `001`
    sample names are kept.
  - `detk-util gather --name-from='/([0-9]+)/' g/*/s.counts.txt | detk-norm deseq2 /dev/stdin`:
    the header is `,001,002` and the rows are `007`, `42`, `0099`.
    `cpm` gives the same result. Both exit 0.
  - `detk-report generate` after stats, filter and norm: the HTML
    contains `"007"` and no `"7"`.
  - `detk-util tidy-counts` with non-numeric sample names keeps `007`.

## Findings

1. **de_toolkit/common.py:350-351 and :353-356, info.** A URL is
   fetched twice: the spy shows two `read_csv` calls on
   `http://.../c.csv`, and `main` made one. The result is correct. The
   cost is a second download of a remote counts file, and a URL that
   serves different content per request (a one-time signed URL) could
   fail or disagree. In that last case the `len(ids) == len(table)`
   guard falls back to pandas' typing; it does not misalign rows. This
   is not worth blocking 1.0 for, and remote input is undocumented. A
   later change could buffer any non-local source too, for example
   with `pandas.io.common.is_url` / `fsspec`.
2. **de_toolkit/common.py:343, info (style).** The comment line is 106
   characters, over the project's 100. Ruff does not flag it, because
   E501 is not selected and the formatter does not rewrap comments. It
   is a leftover from the edit that joined two comments.
3. **tests/common/test_common.py:111, info.** The `~` case is tested.
   The URL case is not; I checked it by hand with a local
   `http.server`. A test could monkeypatch `os.path.exists` or serve a
   file, but this is optional.
4. **Earlier findings: closed.**
   - Second review, finding 1 (URL and `~` regression): fixed, and
     covered by the table above.
   - FIFO, process substitution and `/dev/stdin` (first review): still
     fixed.
   - The fallback test, the whitespace sentence in the CHANGELOG, and
     the scope items recorded in DETK-0015 (tidy-counts/tidy-covs,
     fgsea): unchanged and fine.

## Questions

1. DETK-0015 (still Proposed, Adam's) matches `de.py:248-291,452-478`,
   `transform.py:177,241-269`, `wrapr.py:444,451`, `enrich.py:386` and
   `util.py:804-806`. Two phrases are loose:
   - **Context, around line 46-49.** It says "the R scripts read the
     metadata with `read.csv(row.names=1)` and DESeq2's `stopifnot(...)`
     would ... stop". The `stopifnot` is de_toolkit's own line in the
     deseq2 script (`de.py:291`), not DESeq2's. The Consequences
     already says this correctly. The Context also still reads as if
     every R script stops there.
   - **Consequences, around line 99-101.** It says
     "`vst`/`rlog` build the dataset with `DESeqDataSetFromMatrix`,
     which matches samples by position". `vst` reads no sample info at
     all: `transform.py:178` builds `colData` as `seq(ncol(cnts))`. Only
     `rlog` reads metadata (`transform.py:254`). So sample names cannot
     affect `vst`.

   Neither phrase changes the question or the recommendation, so
   neither blocks this PR. They are for Adam when he settles the
   decision. R is not installed here, so the R behaviour is still read
   from the source rather than run.
2. The acceptance line "007 is kept in every tool's output" is still
   wider than what is delivered, which is the Python side only; the R
   side is DETK-0015. Narrowing the line is Adam's call, at s3.
