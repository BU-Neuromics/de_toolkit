---
kind: step
time: 2026-11-09T21:46:22Z
by: DETK/reviewer
node: release/single-column
step: s2
branch: node/47-single-column
verdict: changes
commits: []
decisions: []
---


# Review of #63: read a one-column input file as one column (#47)

## Summary

The fix works and meets the acceptance. Every reader that sniffed with
`sep=None` in common, util and enrich now goes through `read_delimited`, and
a bare list of IDs (`id`, `gene_id`, `ENSG01.5`, `gene-id`, no header, BOM,
CRLF, `.gz`, FIFO, `/dev/stdin`, URL) reads as one column everywhere. I
probed 40 inputs against origin/main and found no case that got worse in
what is parsed. Comma, tab, semicolon, pipe, space, quoted-comma headers,
R-style counts (missing index field) and R `write.table` default output
(quoted, space-separated) all read the same as on main. A BOM is now
stripped from the first header in `read_delimited`; main kept `﻿g`.
A leading blank line, which errored on main, now reads.

I am asking for two small changes before acceptance, both in scope:

1. `read_id_table` now sniffs twice, so a URL is fetched 4 times instead of
   main's 2. DETK-0020 says "a URL is fetched twice".
2. Pipe loses to space. DETK-0020 lists pipe as a supported delimiter, but a
   pipe table with a space in any header is split on the spaces.

Neither is a regression against main, but (1) makes the decision record
inaccurate, and (2) is a gap in the rule this PR sets.

## Artifacts

- Diff: `origin/main...2a21fd1` (common.py, util.py, enrich.py,
  tests/common/test_read_delimited.py, CHANGELOG, DETK-0020)
- Probe data, script and outputs: `/tmp/claude-1001/-home-adamlabadorf-de-toolkit--claude-worktrees-second-project/332ef69c-eb96-48ee-8873-d8d8be18fdd6/scratchpad/rv63/`
  (`data/`, `scripts/probe.py`, `probe_main.txt`, `probe_branch.txt`).
  main and branch were run from `git archive` copies with the same venv.
- Checks:
  - `uv sync` ok.
  - `uv run pytest`: 344 passed, 49 skipped.
  - `ruff check`: clean. `ruff format --check`: 220 files already formatted.
  - `mkdocs build --strict`: ok.
  - `gh pr checks 63`: all pass except `test with R (bioconda)`, which was
    still pending (0s) when I checked.

### main vs branch

RD is the sniffed read (`pandas.read_csv(sep=None)` on main,
`read_delimited` on the branch). RID is `read_id_table`.

| input | main | branch |
|---|---|---|
| `id` + IDs | RD cols `Unnamed: 0`,`d` | 1 col `id` (better) |
| `gene_id` + IDs (also `.gz`, BOM, FIFO, stdin, URL) | `g`,`n`,`_id` | 1 col (better) |
| `ENSG01.5` (no header) | `EN`,`G01.5`; RID index `EN`,`EN` | 1 col (better) |
| `gene-id` | `g`,`n`,`-id` | 1 col (better) |
| `id` CRLF | `Unnamed: 0`,`d` | 1 col (better) |
| BOM on comma table | RD header `﻿g` | `g` (better) |
| leading blank line | error "Could not determine delimiter" | reads (better) |
| `gene id` one column | 2 cols `gene`,`id` | same (unchanged) |
| `Gene stable ID` (BioMart) one column | 3 cols | same (unchanged) |
| comma / tab / semicolon / pipe / single space | correct | same |
| double space | empty `Unnamed` columns | same |
| `"gene, id",s1,s2` | correct | same |
| `"gene id"` one column, quoted | 1 col | same |
| R-style counts, comma and tab (missing index field) | correct | same |
| R `write.table` default (`"s1" "s2"` / `"g1" 1 2`) | correct | same |
| header `g\tsample,1\tsample,2` | split on comma (wrong) | same |
| header `g,sample\t1,s2` | comma (right) | same |
| `g\|sample 1\|sample 2` | split on space (wrong) | same: still wrong |
| `g;sample 1` / `g\tsample 1` | correct | same |
| R-style one-sample (`s1` / `A\t1`) | wrong (`Unnamed: 0`,`1`) | wrong differently (1 col, index `A\t1`) |
| `g:s1:s2` (colon) | 3 cols | 1 col (worse, documented in DETK-0020) |
| header-only, comma | (0,3) | same |
| header-only `gene_id` | (0,3) `g`,`n`,`_id` | (0,1) (better) |
| empty file | csv.Error | EmptyDataError (both fail) |
| URL, `read_delimited` | 1 GET | 2 GETs |
| URL, `read_id_table` | 2 GETs | 4 GETs (worse) |
| gzip bytes on `/dev/stdin` | UnicodeDecodeError | same (no name to infer from) |

## Findings

1. **Medium**: `de_toolkit/common.py:433-441` (`read_id_table`) together with
   `de_toolkit/common.py:403-405` (`_read_sniffed`). `read_id_table` calls
   `_read_sniffed` twice, and each call re-reads the first line. For a URL
   that means 4 full downloads (pandas reads the whole response), where
   main did 2. I measured this with a local HTTP server: main sent 3
   requests and the branch 6 for `read_delimited` plus `read_id_table`.
   DETK-0020's Consequences say "a URL is fetched twice", which is wrong for
   the counts and column-data path. It also gets worse for single-use or
   slow URLs.
   **Fix:** sniff once in `read_id_table` and pass `sep` to both parses
   (e.g. split `_read_sniffed` into sniff and read). Ideally also buffer
   URLs in `_rewindable` so every reader fetches once.

2. **Low-Medium**: `de_toolkit/common.py:325` and `:339`
   (`SNIFF_DELIMITERS` / `sniff_delimiter`). `csv.Sniffer`'s preference
   order is `, \t ; ' ' :`, and pipe is not in it. Any pipe table whose
   header contains a space is therefore split on spaces:
   - `g|sample 1|sample 2` gives columns `g|sample`,`1|sample`,`2`.
   - In `read_id_table`, index `A|1|2`.
   - BioMart-style `Gene stable ID|Gene name` behaves the same way.

   The run exits 0. This is the same on main, but this PR declares pipe a
   supported delimiter and DETK-0020 says comma, tab and semicolon are
   preferred over space, which leaves pipe out.
   **Fix:** prefer pipe over space, e.g. if the sniffer returns `' '` and
   the line contains `|`, use `|`. Add a test with a space in a pipe
   header.

3. **Low** (trade-off, no change requested here): a one-column file whose
   header has a space (`gene id`, BioMart's `Gene stable ID`) is still
   split into empty extra columns. This is the same as main, and the
   realistic input for it is a gene list for `detk-util annotate`.
   - I would keep space in the set. R's `write.table` default output is
     quoted and space-separated, a plausible detk counts or sample-info
     input, and it reads only because space is in the set. Dropping space
     would make that file one column, which is a real regression.
   - A cheap refinement: accept space only when the second line splits
     into the same number of fields, or one more (R-style). That fixes
     `gene id` and `Gene stable ID` and keeps `write.table`.
   - That would amend DETK-0020, so it is a human call; see Questions.

4. **Low**: a one-sample R-style counts file (header `s1`, rows `A\t1`)
   reads as one column with IDs `A\t1` and exits 0. The first line has no
   delimiter. Main was also wrong here. The same second-line check would
   catch it. Edge case, follow-up at most.

5. **Low**: a tab file with a comma in a header field
   (`g\tsample,1\tsample,2`) is split on comma. This is the sniffer's
   preference order, unchanged from main and outside #47. It could fold
   into the fix for finding 2 if a deterministic order is preferred, e.g.
   tab before comma when both occur.

6. **Info**: `de_toolkit/norm.py:403` (`read_lengths`) still uses
   `sep=None`, outside this node's scope. The two-column requirement turns
   any mis-sniff into an error, not silent damage, so the risk is low. A
   small follow-up to move it onto `read_delimited` for consistency is
   worthwhile. I would not file it as a bug.

7. **Info**: tests (`tests/common/test_read_delimited.py`) cover `id` and
   `gene_id` with and without a header across all callers, and comma, tab
   and semicolon regressions. Not covered:
   - pipe and space tables
   - a quoted header with a space
   - R `write.table` output
   - a URL (fetch count)

   Adding pipe-with-space and `write.table` would pin the behaviour behind
   findings 2 and 3. The CHANGELOG entry is accurate.

## Questions

- Should DETK-0020 adopt the second-line check for space (finding 3)? Or
  should the space-in-header trade-off stand as documented ("revisit if a
  user reports either")?
- Should a URL be buffered once in memory, like a FIFO, so that sniffing
  never costs a second download?
- `test with R (bioconda)` was still pending at review time. It should
  pass before acceptance.
