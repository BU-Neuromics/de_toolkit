---
kind: step
time: 2026-11-09T21:54:58Z
by: DETK/reviewer
node: release/single-column
step: s2
branch: node/47-single-column
verdict: changes
commits: []
decisions: []
---


# Re-review of #63: read a one-column input file as one column (#47)

## Summary

Both changes asked for in the first review are in fcf5ed0 and work as
described. `read_id_table` sniffs once and fetches a URL once.
`read_delimited` also fetches a URL once. Pipe now beats space:
`g|sample 1|sample 2` and BioMart's `Gene stable ID|Gene name` read on pipe,
and R `write.table` output still reads on space. DETK-0020 and the CHANGELOG
match the code.

On the earlier probe's 40 inputs, the branch differs from the first review's
`probe_branch.txt` only on `pipespace.txt`, which is now correct. main is
unchanged. FIFO, `/dev/stdin` (from a pipe and from a file), process
substitution (plain and `zcat`), `~/`, local `.gz`, text and binary file
handles, and `file://` `.gz` all read as on main. Padded IDs (`007`) stay
text in `read_id_table` through every one of those routes and through HTTP.

The new URL buffering has one regression, and I am asking for it to be fixed
before acceptance. A URL whose name ends in `.gz` and whose server sends
`Content-Encoding: gzip` gets decompressed twice and now fails with
`BadGzipFile`. main read it. The fix is one line plus a test (finding 1).

## Artifacts

- Diff: `origin/main...fcf5ed0`. `origin/main` is 74632ba, which has moved
  since the branch point (CI and CHANGELOG only, #60).
  `git merge-tree --write-tree origin/main HEAD` gives a clean tree
  (432cc7c).
- Scratch: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rr63/`
  - `main/` and `branch/`: `git archive` copies, run with `PYTHONPATH` set to
    each, using the worktree's venv (pandas 3.0.5).
  - `probe_main.txt`, `probe_branch.txt`: the earlier probe
    (`rv63/scripts/probe.py`) rerun on `rv63/data`.
  - `scripts/srv.py`: a counting `http.server`. Files named `enc_*` are sent
    with `Content-Encoding: gzip`.
  - `scripts/urlprobe.py`: counts GETs per read. `scripts/local.py` probes
    local sources.
  - `local.txt`: local sources. `edge_main.txt`, `edge_branch.txt`: pipe and
    space edge cases.
  - `checks.txt`: check output.

### GETs per read (local http.server)

These counts held for every URL served: `comma.csv`, `comma.csv.gz`,
`gene_id.txt`, `gene_id.txt.gz`, `enc_gene_id.txt`, `enc_comma.csv.gz` and
`padded.csv`.

| reader | main | 2a21fd1 (first review) | fcf5ed0 |
|---|---|---|---|
| `read_delimited` (main: `read_csv(sep=None)`) | 1 | 2 | 1 |
| `read_id_table` | 2 | 4 | 1 |

### URL content

| URL | main | fcf5ed0 |
|---|---|---|
| `comma.csv`, `comma.csv.gz` (gzip by name) | 3 cols | 3 cols |
| `gene_id.txt`, `gene_id.txt.gz` | split `g`,`n`,`_id` | 1 col |
| `enc_gene_id.txt` (gzip bytes, `Content-Encoding: gzip`, plain name) | split | 1 col |
| `enc_comma.csv.gz` (gzip bytes, `Content-Encoding: gzip`, `.gz` name) | 3 cols | **BadGzipFile** |
| `padded.csv` via `read_id_table` | `007`,`010` | `007`,`010` |

### Pipe vs space (`edge_*.txt`)

| input | main | fcf5ed0 |
|---|---|---|
| `g\|sample 1\|sample 2` | `g\|sample`,`1\|sample`,`2` | `g`,`sample 1`,`sample 2` |
| `Gene stable ID\|Gene name` | 4 cols | 2 cols, right |
| R `write.table` default `"s1" "s2"` | right | right |
| `"a\|b" "c"` (quoted `\|` in a space table) | right | right |
| `a\|b c` (`write.table(quote=FALSE)`, `\|` in a name) | right | split on pipe (finding 2) |
| `id\|x` / `007\|1` | right, `007` kept | same |

### Checks

- `uv sync`: ok.
- `uv run pytest`: 354 passed, 49 skipped.
- `ruff check`: clean. `ruff format --check`: 222 files already formatted.
- `mkdocs build --strict`: ok.
- `gh pr checks 63`: all pass except `test with R (bioconda)`, which is still
  in progress (run 42706193954, started 21:50:04Z). It must pass before
  acceptance.

## Findings

1. **Medium (regression, change requested):** `de_toolkit/common.py:368-376`
   (`_rewindable`).
   - **What happens:** the URL is opened with
     `get_handle(name, "rb", compression=None, ...)`, and the buffer is then
     read with compression inferred from the name. For an HTTP
     `Content-Encoding: gzip`, pandas' opener already decompresses the body
     (pandas `io/common.py:406-410` overrides the compression). A `.gz` name
     then makes the read decompress a second time.
   - **Result:** `http://.../counts.csv.gz` served as gzip bytes with
     `Content-Encoding: gzip` (an S3 object uploaded with
     `ContentEncoding=gzip`, for example) fails with
     `BadGzipFile: Not a gzipped file (b'g,')` in both `read_delimited` and
     `read_id_table`. main read it.
   - **Why it matters:** the code comment says the opener is used so that
     Content-Encoding is handled as before, so the claim is only half true.
     It fails loudly, not silently.
   - **Fix (verified in scratch):** let pandas decide, exactly as it did
     before, and read the buffer uncompressed:
     ```python
     with pandas.io.common.get_handle(name, "rb", compression="infer", is_text=False) as h:
         return io.BytesIO(h.handle.read()), None
     ```
     With this, `comma.csv.gz`, `enc_comma.csv.gz`, `enc_gene_id.txt`, and
     `file://...gz` all return the decompressed bytes. The name-based
     inference is then needed only for the FIFO branch.
   - **Test:** add one next to `tests/common/test_read_delimited.py:185-205`.
     Serve gzip bytes under a `.gz` name with `Content-Encoding: gzip`.

2. **Low (trade-off, no change requested):** `de_toolkit/common.py:339-349`
   (`sniff_delimiter`).
   - **What happens:** the pipe preference is the mirror image of the old
     bug. A space-separated file whose first line has an unquoted `|`, such
     as `write.table(quote=FALSE)` with a sample named `a|b`, is now split on
     the pipe. `a|b c` reads as columns `a`,`b c`, with index `g1 1 2`, and
     exits 0. main read it right.
   - **How likely:** much rarer than BioMart's pipe export, and
     `write.table`'s default (quoted) output is unaffected.
   - **What to do:** accepting it is reasonable. Recording it in DETK-0020's
     Consequences, next to `gene id`, would make the rule's known cost
     complete.

3. **Info:** buffering a URL in memory is acceptable.
   - For `http`, `https` and `ftp`, pandas already reads the whole response
     into a `BytesIO` (pandas `io/common.py:410`), so main held it in memory
     too.
   - The branch adds a transient second copy of the compressed bytes
     (`BytesIO(h.handle.read())` copies the handle's buffer).
   - Only fsspec URLs (`s3://`, `gs://`) used to stream and are now held
     whole.
   - Both are small next to the parsed frame from the python engine, and
     detk's inputs (counts, sample info, result tables) are at most a few
     hundred MB. No change needed. A sentence in the docstring would do if
     anyone asks.

4. **Info:** tests cover the single fetch for both readers, pipe with spaces
   in headers, and R `write.table` counts. These were the gaps in the first
   review. The CHANGELOG entry is accurate.

## Questions

- Should finding 2 (an unquoted `|` in a space-separated header) be added to
  DETK-0020's Consequences as a known cost of preferring pipe?
