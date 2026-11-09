---
kind: step
time: 2026-11-09T20:13:38Z
by: DETK/reviewer
node: release/padded-ids
step: s2
branch: node/48-padded-ids
verdict: changes
commits: []
decisions: []
---


# Review of #56: read feature IDs as text in the shared reader

## Summary

`read_id_table` does what it says for files and streams: across 28
hand-written edge cases and a 20,000-file fuzz against the old reader,
the IDs never ended up on the wrong rows. The counts and covariates
match the old reader's in every case, and `007`, Entrez, versioned and
`1e5` IDs and padded sample names come through `detk-norm`
(deseq2/tpm/fpkm), `detk-filter` (with sample info), `detk-stats`
(rowdist/summary/pca), `detk-transform plog`, `detk-outlier`,
`detk-util tidy` and `detk-report generate` as written. The cost is
1.2-1.3x the old read time on 60k-row files and nothing on wide ones.
All checks are green.

I am asking for changes for one regression. The table is now parsed
twice, so a path that can be read only once fails: a FIFO, process
substitution `<(zcat counts.gz)` or a piped `/dev/stdin`. Every command
built on `CountMatrixFile` then exits 1 with no message, where `main`
read these inputs correctly. The fix is small: buffer any path that is
not a regular file, as the code already does for streams. The other
findings are gaps in the acceptance and in DETK-0015, not defects in
this diff.

## Artifacts

- Checks: `uv sync` ok; `uv run pytest`: 241 passed, 49 skipped;
  `ruff check` clean; `ruff format --check` clean (162 files);
  `mkdocs build --strict` ok; `gh pr checks 56`: all 11 pass,
  including "test with R (bioconda)".
- Break attempts (scratch rv56/brk.py, cmp.py, fuzz.py, min.py,
  shrink.py). Each case below was checked against the old reader on
  `origin/main`.
  - Header variants: named, empty (`,a,b`), quoted-empty and R-style
    missing index field (`a\tb` over `007\t1\t2`). All aligned, `007`
    kept.
  - Quoted separator (`"0,07"`), a quoted newline in the ID or in a
    data field, CRLF, blank lines, whitespace-only lines,
    separator-only lines (NaN ID kept in place), duplicate IDs,
    `NA`/empty IDs (missing, as before), a trailing separator, short
    and long ragged rows, header-only, a single column, space and
    semicolon separators, no final newline, trailing blank rows. All
    aligned, values identical to the old reader.
  - BOM: works. The index name is `﻿id`, the same as before.
  - Comment line or quoted newline in the header: the sniffer
    misreads them, but identically to before; no new failure.
  - `.gz` path, text and binary handles: ok.
  - FIFO, process substitution, piped `/dev/stdin`: fail (finding 1).
    `-` is not supported, before or after.
  - Fuzz: 20,000 random files. None misaligned, and none fails only on
    the new reader. 321 take the length-mismatch fallback, every one
    degenerate (a row with 2+ more fields than the header, which pandas
    turns into a MultiIndex).
  - Performance: 60000x12 0.30 -> 0.39 s, 60000x100 2.20 -> 2.67 s,
    2000x2000 1.61 -> 1.54 s.
- Real commands with `007`, `5290`, `ENSG00000000003.14`, `0001.10`,
  `1e5` and samples `001..004`: ids and sample names kept everywhere
  except `detk-util tidy-counts`/`tidy-covs` (finding 2).

## Findings

1. **de_toolkit/common.py:322-332, medium (regression).** The second
   `pandas.read_csv` opens a path again, so a path that can be read
   only once is consumed by the first parse. With a FIFO, `<(zcat
   counts.gz)` or `cat counts | detk-norm deseq2 /dev/stdin`, the
   second parse raises `csv.Error: Could not determine delimiter`, and
   `make_cli_count_obj` exits 1. It does so silently, because the
   error is logged before `set_logging` runs (common.py:100, which is
   older than this PR). `origin/main` reads the same inputs.
   Suggested fix: treat a path that is not a regular file
   (`not os.path.isfile(f)`, or `stat.S_ISREG`) like a stream and read
   it into a buffer once. Handle compression explicitly in that case,
   or open it with pandas' own handle. Add a test with `os.mkfifo` or a
   pipe.
2. **de_toolkit/util.py:390-392, low (acceptance gap, out of scope).**
   `detk-util tidy-counts` and `tidy-covs` read both files again with a
   plain `read_csv(index_col=0)` and compare `covs.index` with
   `counts.columns`. With sample names `001..004` the comparison is
   int against text, and both exit 1 ("requires that all row IDs...").
   It failed on main too, but `tidy` now works and these two do not.
   This needs either a one-line switch to `read_id_table` or a
   follow-up.
3. **de_toolkit/enrich.py:386, low (acceptance gap, not in
   DETK-0015).** `detk-enrich fgsea` reads the result file with a
   plain `read_csv`, so a result whose ID column is all numeric turns
   `007` into `7` before it reaches fgsea, and it then no longer
   matches `007` in the GMT. DETK-0015 lists only de deseq2/firth and
   transform vst/rlog. `util annotate` already reads as text and is
   fine.
4. **de_toolkit/common.py:333-336, low.** The fallback branch has no
   test, and its warning goes through the same pre-`set_logging` path,
   so at the CLI it is never shown. A user whose IDs silently become
   `7` again gets no sign of it. In the fuzz it is reached only by
   malformed rows, so this is low.
5. **de_toolkit/norm.py:337-345, info (scope).** This is a
   docstring-only change in a file outside the node's scope
   (common.py, tests/common/, docs/tools/norm.md, CHANGELOG). It is
   harmless and accurate, but outside the scope as written.
6. **de_toolkit/common.py:332, info (behaviour change).** Whitespace
   around a numeric ID is now kept (`" 007"` stays `" 007"`, where it
   used to become `7`). This matches how text IDs were always
   treated, and it is consistent, but the CHANGELOG could say "exactly
   as written, including whitespace".

## Questions

- DETK-0015 is a fair statement for the four R commands, and option 2
  (a follow-up node with an R-gated round-trip test) is sound. Two
  qualifications:
  - The problem is narrower than it reads. R's `type.convert`, like
    pandas, turns `007` into `7` only when the whole ID column looks
    numeric. A mixed column (Ensembl plus `007`) keeps `007` in R and
    in wrapr's read-back.
  - It is broader in one respect: `detk-enrich fgsea` (finding 3) and
    `detk-util tidy-counts`/`tidy-covs` (finding 2) are also tools
    where it fails. An all-numeric versioned column (`1.10`, `1.1`)
    also collapses into duplicate row names in R.
- Acceptance line 1 ("007 is kept in every tool's output") is only
  partly met. It holds for the reader and for every Python command on
  the counts path. It does not hold for the four R commands, enrich
  fgsea, or tidy-counts/tidy-covs with padded sample names. I suggest
  narrowing it to "every command that reads counts in Python" and
  moving the rest into DETK-0015's follow-up, if Adam takes option 2.
  Acceptance line 2 (norm.md) holds.
