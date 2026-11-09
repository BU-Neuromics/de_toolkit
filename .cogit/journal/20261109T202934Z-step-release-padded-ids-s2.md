---
kind: step
time: 2026-11-09T20:29:34Z
by: DETK/reviewer
node: release/padded-ids
step: s2
branch: node/48-padded-ids
verdict: changes
commits: []
decisions: []
---


# Re-review of #56: read feature IDs as text in the shared reader

## Summary

The earlier regression is fixed. A FIFO (plain and `.gz`), `<(zcat
counts.csv.gz)`, `<(cat counts.csv)` and a piped `/dev/stdin` all read
correctly now and keep `007`. Regular files still take the two-parse
path, and so does `/dev/stdin` when it is redirected from a regular
file. The new fallback test is sound. The merge with main is right:
the padded-ID fpkm test expects main's corrected formula, and
`gather` into `detk-norm` keeps `007`, `0099` and the sample names
`001`/`002`, including through a pipe. The CHANGELOG's whitespace
sentence is accurate. The earlier 20,000-file fuzz gives the same
result as before, and all checks pass.

I am asking for changes for one new regression, which the fix
introduced. The fix buffers every path for which `os.path.isfile` is
false. That includes paths that are not local files at all, which
pandas read on `main`: `http(s)://`, `file://` and other URLs, and an
unexpanded `~/counts.csv`. These now fail with `FileNotFoundError`,
and at the CLI the command exits 1 with no message. With the URL,
`main` printed the table. The fix is one line, and I tested it:
buffer only a path that exists and is not a regular file.

DETK-0015's revised text is accurate, apart from one overstatement
about sample names (question 1).

## Artifacts

- Checks at b30c683 (`origin/main` 081b3e8 is an ancestor):
  - `uv sync`: ok.
  - `uv run pytest`: 302 passed, 49 skipped.
  - `ruff check`: clean.
  - `ruff format --check`: 180 files already formatted.
  - `mkdocs build --strict`: ok.
  - `gh pr checks 56`: all 10 pass, including "test with R (bioconda)" (7m19s).
- Non-regular paths at the CLI (`detk-norm cpm` on `001..003` x
  `007,42,0099`; scratch `rr56/`):
  - Process substitution `<(zcat c.csv.gz)` and `<(cat c.csv)`: ok,
    `007` kept.
  - `cat c.csv | ... /dev/stdin`: ok.
  - `/dev/stdin < c.csv`: ok. `isfile` is true here, so this takes
    the two-parse path.
  - FIFO `f.csv` and FIFO `f.csv.gz`: ok.
  - Gzip bytes piped to `/dev/stdin`, a name without `.gz`: exit 1.
    `main` gives the same result, so this is not a regression.
- Two-parse path for a regular file: a `read_csv` spy shows two calls,
  both on the path string. No buffer is used.
- Merge with main:
  - `test_padded_ids_match_lengths_file[fpkm]` expects
    `count*1e9/(length*colsum)`, which is main's `fpkm`.
  - By hand, `detk-util gather --name-from='/([0-9]+)/' ... | detk-norm
    deseq2 /dev/stdin` gives the header `,001,002` and the rows `007`,
    `42`, `0099`.
- The CHANGELOG's whitespace sentence:
  - An all-numeric ` 007`/`42 ` column gives `[' 007', '42 ']` on this
    branch and `['7', '42']` on main. The sentence holds.
  - A mixed column kept the whitespace on main as well, as the
    sentence's "text IDs always kept it" says.
- Fuzz: rv56/fuzz.py, rerun unchanged. ok 13221, fallback 321,
  mismatch 0, new-only errors 0. This is identical to the first
  review.
- Inputs that are not local files (rr56/probe.py, `CountMatrixFile`):

  | input | main | this branch | with the suggested fix |
  |---|---|---|---|
  | `http://localhost/c.csv` | ok | FileNotFoundError | ok, `007` kept |
  | `http://localhost/c.csv.gz` | ok | FileNotFoundError | ok |
  | `file:///.../c.csv` | ok | FileNotFoundError | not run |
  | `'~/c.csv'` (unexpanded) | ok | FileNotFoundError | ok |

  With the suggested fix, the FIFO `.gz`, `/dev/stdin` and a missing
  path (FileNotFoundError, as before) are unchanged.
- Sample names in Python (`CountMatrixFile` with a design):
  - `001..003` and `1..3` work on this branch.
  - Both raise `SampleMismatchException` on main.
  - `detk-util tidy-counts` with `001..003` still exits 1. This is
    recorded in DETK-0015.

## Findings

1. **de_toolkit/common.py:340, low-medium (regression in the fix).**
   `elif not os.path.isfile(f)` also catches paths that are not local
   files: URLs (`http(s)://`, `ftp://`, `s3://`, `file://`) and an
   unexpanded `~`. `open()` cannot read either one. On main,
   `pandas.read_csv` read both, because it fetches URLs and expands
   `~`. Neither form is documented, but `detk-norm cpm
   http://.../c.csv` printed the table on main. It now exits 1 with
   no message, because the error is logged before `set_logging`.
   Suggested fix, which I tested:
   `elif os.path.exists(f) and not os.path.isfile(f):`. Everything
   else then goes to pandas as before, including a missing path. A
   short test with a `~` path (monkeypatch `HOME`) would cover this.
2. **Earlier finding 1 (FIFO, process substitution, piped
   `/dev/stdin`): fixed.**
   - `test_read_id_table_fifo` covers plain and `.gz`, with a
     timeout.
   - `test_cli_reads_counts_from_dev_stdin` runs a subprocess with
     the counts piped in.
   - Both pass, and I confirmed both cases by hand.
   - Compression comes from the name in pandas' order and is
     case-insensitive, as pandas does it.
3. **Earlier finding 4 (the fallback is untested): fixed.**
   `test_read_id_table_falls_back_when_parses_disagree` checks that
   the table matches pandas' own typing and that the warning is
   logged. The warning is still not shown at the CLI, because logging
   is set up after the read. That is out of scope.
4. **Earlier finding 6 (whitespace in the CHANGELOG): fixed.** The
   sentence is accurate (see Artifacts).
5. **Earlier findings 2 and 3 (tidy-counts/tidy-covs, enrich fgsea):
   recorded in DETK-0015, as agreed.** They are out of scope here.
6. **Earlier finding 5 (norm.py docstring outside the scope): left as
   is.** It is accurate. This is info only.

## Questions

1. DETK-0015 (revised) is accurate against `de.py` and `transform.py`
   (the R is embedded there; there are no `.R` files),
   `wrapr.py:444,451`, `enrich.py:386` and `util.py:804-806,816-838`.
   It is right on several points:
   - deseq2 and firth read with `read.csv(header=T, as.is=T)` and
     `rownames(cnts) <- cnts[[1]]`. vst and rlog read with
     `read.csv(row.names=1)`. In each case `type.convert` runs before
     the column becomes row names.
   - A mixed column survives.
   - A duplicate `1.1` stops on the row names.
   - wrapr re-types the output with `read_csv(index_col=0)`.
   - fgsea reads with a plain `read_csv`.
   - tidy-counts/tidy-covs re-read and compare as int against text.
     I confirmed by hand that they exit 1.
   - annotate reads as `dtype=str`.
   - Before #48, plain numeric sample names failed in Python. I
     confirmed this on main.

   One overstatement is in the Consequences. "Zero-padded sample
   names stop at DESeq2's sample check" holds only for `detk-de
   deseq2` (`de.py:291` `stopifnot`). `firth` has no such check.
   `vst`/`rlog` pass the metadata to `DESeqDataSetFromMatrix`, whose
   name check stops only when the colData row names are all among
   the count columns, which `1` vs `001` is not. These three should
   therefore run, with the metadata matched by position. That
   behaviour comes from reading DESeq2's source; R is not installed
   here, so I could not run it. I suggest saying "stop in `detk-de
   deseq2`". This is for Adam; it does not block this PR.
2. The acceptance line "007 is kept in every tool's output" still
   reads wider than what is delivered. I leave narrowing it to Adam,
   with DETK-0015.
