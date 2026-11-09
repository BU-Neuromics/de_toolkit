---
kind: step
time: 2026-11-09T22:05:21Z
by: DETK/reviewer
node: release/single-column
step: s2
branch: node/47-single-column
verdict: approve
commits: []
decisions: []
---


# Third review of #63: read a one-column input file as one column (#47)

## Summary

The PR meets the node's acceptance: a bare list of IDs reads as one column in every reader that sniffs the delimiter (`read_id_table` in common, `annotate` and `tidy-counts`/`tidy-covs` in util, and the fgsea result in enrich), with tests.

The one change asked for in the second review is in 1d0a907, with a formatting commit after it (6efb688). `_rewindable` now opens a URL through `pandas.io.common.get_handle(..., compression="infer")` and reads the buffer uncompressed. A `.gz` URL served with `Content-Encoding: gzip` is decompressed once and reads as it does on main.

The new test `test_url_with_content_encoding_gzip` fails on fcf5ed0 (`counts.csv.gz` case) and passes now. Every URL case I served reads as on main, apart from the intended one-column fix. Each reader fetches a URL once. `007` is kept.

The pipe-over-space trade-off asked for in the second review's finding 2 is now recorded in DETK-0020's Consequences, together with how a URL is decompressed. Local sources behave as on main, and the 41-file probe is unchanged from the second review.

All local checks pass, and all CI checks pass, including `test with R (bioconda)` on 6efb688.

I approve.

## Artifacts

- Diff: `origin/main...6efb688`. `origin/main` is 74632ba.
  - `git merge-tree --write-tree origin/main HEAD` gives a clean tree.
  - GitHub reports the PR `MERGEABLE`.
  - Since the second review (`9c51e83..6efb688`) the code change is 5 lines in `de_toolkit/common.py`, plus one parametrized test and the DETK-0020 revision.
- Scratch: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/r3-63/`
  - `main/`, `prev/` (fcf5ed0), `branch/` (6efb688): `git archive` copies, each run with `PYTHONPATH` set to it and the worktree's venv.
  - `url.txt`: URL reads and GET counts (`scripts/srv.py` and `scripts/urlprobe.py`; files named `enc_*` are sent with `Content-Encoding: gzip`).
  - `file.txt`: `file://` URLs.
  - `probe_main.txt`, `probe_branch.txt`: the probe on all of `rv63/data`.
  - `edge_*.txt`: pipe and space cases.
  - `local_*.txt`: local sources.
  - `checks.txt`, `fmt.out`: check output.

### URL reads (local `http.server`; RD is `read_delimited` (main: `read_csv(sep=None)`), RID is `read_id_table`)

| URL (served as) | main | fcf5ed0 | 6efb688 |
|---|---|---|---|
| `comma.csv` (plain) | 3 cols | 3 cols | 3 cols |
| `comma.csv.gz` (gzip, by name) | 3 cols | 3 cols | 3 cols |
| `enc_comma.csv` (gzip bytes, CE gzip, plain name) | 3 cols | 3 cols | 3 cols |
| `enc_comma.csv.gz` (gzip bytes, CE gzip, `.gz` name) | 3 cols | **BadGzipFile** | 3 cols |
| `enc2_comma.csv.gz` (double gzip, CE gzip) | UnicodeDecodeError | same | same |
| `gene_id.txt`, `gene_id.txt.gz` | split `g`,`n`,`_id` | 1 col | 1 col |
| `enc_gene_id.txt` | split | 1 col | 1 col |
| `enc_gene_id.txt.gz` | split | **BadGzipFile** | 1 col |
| `padded.csv`, `padded.csv.gz`, `enc_padded.csv` via RID | `007`,`010` | `007`,`010` | `007`,`010` |
| `enc_padded.csv.gz` via RID | `007`,`010` | **BadGzipFile** | `007`,`010` |
| `file://` `comma.csv.gz`, `padded.csv(.gz)` | right, `007` kept | | same as main |
| `file://` `gene_id.txt.gz` | split | | 1 col |

GET counts held for every URL above:

| reader | main | 6efb688 |
|---|---|---|
| RD | 1 | 1 |
| RID | 2 | 1 |

### Probe (`rv63/data`, 41 files, both readers)

- `probe_main.txt` and `probe_branch.txt` are byte-identical to the second review's `rr63/probe_*.txt`.
- main and branch differ only where intended or recorded:
  - The one-column files read as one column: `id`, `gene_id`, `gene_id.gz`, `bom_one`, `crlf_one`, `dash`, `versioned`, `noheader`, `headeronly_one`, `leadblank`, `rstyle_one`.
  - The pipe tables now read right: `pipespace`, `biomart_pipe`.
  - The BOM is stripped from `bom.csv`'s first header.
  - `empty.txt` raises `EmptyDataError` instead of "Could not determine delimiter".
  - `colon.txt` is one column, as DETK-0020 records.
- The edge set (`rr63/edge`) is identical to the second review on both sides. The R `write.table` output, quoted or not, reads right. The one cost, `a|b c` (unquoted `|` in a space table), now splits on the pipe and is recorded in DETK-0020.

### Local sources (`local_*.txt`)

- `padded.csv` and `gene_id.txt` were read through these routes:
  - a FIFO, plain and gzip
  - `/dev/stdin` from a file and from a pipe
  - process substitution through `zcat`
  - `~/`
  - a local path and a local `.gz`
  - `StringIO`, `BytesIO` and `open()` handles
- Every route reads as on main, apart from the one-column fix. `007` stays text in `read_id_table` everywhere.

### Checks

- `uv sync`: ok.
- `uv run pytest`: 356 passed, 49 skipped.
- `uv run ruff check .`: all checks passed.
- `uv run ruff format --check .`: exit 0, 224 files already formatted.
- `uv run --group docs mkdocs build --strict`: ok.
- New test against fcf5ed0's code: `test_url_with_content_encoding_gzip[counts.csv.gz]` fails with `BadGzipFile`. All 5 URL tests pass on 6efb688.
- `gh pr checks 63`: all 10 pass on 6efb688, including `test with R (bioconda)` and `combined coverage` (run 42707263045).

## Findings

1. **Low (no change requested):** `de_toolkit/common.py:369-377` (`_rewindable`).
   - For a URL, `compression` is computed from the name and then discarded, because the URL branch returns `None`.
   - Moving the `next(...)` below the `if is_url:` return would make it plain that name inference now serves only the FIFO path.
   - This is cosmetic.

2. **Info:** no PR comment answers the second review's changes.
   - The only PR comment covers the first review's fixes.
   - What changed in 1d0a907 is recorded only in the commit message and DETK-0020's history.
   - For the human at s3, a one-line comment would help. It is not a blocker.

3. **Info:** `read_delimited(f, compression=...)` would raise `TypeError` (multiple values), because `_read_with` passes `compression` itself.
   - No caller passes it.
   - Note it if the helper is ever used more widely.

## Questions

- None blocking. Adam's open question in DETK-0020, whether to check the second line before choosing space, stays with him.
