---
template: adr
state: Proposed
authority: [human]
date: 2026-11-22
from: {node: release/short-header, step: s2}
applies: [release/short-header]
---

# A one-field header over unquoted space-separated rows: one column or two

## Background

detk guesses a table's delimiter. Before #136, a first line with none of
`SNIFF_DELIMITERS` (comma, tab, semicolon, pipe, space) meant a
one-column table, such as a bare list of sample IDs (DETK-0020). R's
`write.table` leaves out the header cell over the row names. So a
one-column sample sheet written by R has a header of one field over rows
of two: `"condition"` over `"S1","a"`. That layout was read as one column
and failed. PR #138 fixes this: when the first line has no delimiter, the
delimiter is guessed from the first data line instead, and the table is
one column only when that line has none either (outside quotes).

Space is one of the delimiters. An *unquoted* one-column list whose first
ID has a space in it (`sample` over `ctrl 1`) now reads as
space-separated. Excel and most tools do not quote a CSV field just
because it has a space, so an exported list like this is not quoted.

## Context

Reviewer reproduction on the PR head (b18d918). Counts are
`gene,ctrl 1,S2,S3`. The column data is `sample` / `ctrl 1` / `S2` / `S3`.

- On main (06c6a10), `detk-util tidy -p` keeps all three samples. The
  column data is the IDs `ctrl 1`, `S2`, `S3`.
- On the PR, the column data reads as IDs `ctrl`, `S2`, `S3` with a column
  `sample` = `1`, NaN, NaN. pandas fills in the ragged rows without an
  error. `tidy` exits 0, drops sample `ctrl 1` from the counts, and writes
  a column data with a made-up `sample` column. The only sign is an INFO
  log line, `counts columns lost: 1`. This is a silent wrong result.
- When *every* ID has a space (`sample 1`, `sample 2`), the IDs come out as
  `sample`, `sample` and tidy stops with "No sample names were found to be
  in common". That failure is loud but confusing, and it is a regression
  from main, which read the list correctly.
- When the space comes in a later line (`S2`, `ctrl 1`, `S3`), the list
  stays one column, because only the first data line is guessed from.
  So whether a list reads correctly depends on the order of its rows.

The layout #136 must read: R's default `write.table(sep=" ")` quotes its
fields (`"condition"` / `"S1" "a"`), so the delimiter there is a space
*outside quotes*. Only `quote=FALSE` with `sep=" "` gives unquoted
`condition` / `S1 a`, which cannot be told apart from an ID list with
spaces.

Criteria: (1) no silent wrong result for a plausible input; (2) the R
layouts named in #136's acceptance read correctly (comma and tab, quoted
and unquoted); (3) a rule simple enough to document.

## Options

**A. Keep the PR as it is.** Any delimiter, space included, found on the
first data line makes a two-column table. Meets (2) fully and also reads
R's `quote=FALSE, sep=" "`. Fails (1): an unquoted ID list whose first ID
has a space is silently mis-split, and the result depends on the order of
its rows.

**B. From the data line, accept space only outside quoted fields, and
require the rows to agree.** A delimiter found on the first data line is
used only when (i) it is not space, or the line's fields are quoted, as
R's default writes them; and (ii) the first data lines (for example up to
the first 10 lines read for the sniff) all split into the same number of
fields, at least 2. Otherwise the table is one column, as on main. Meets
(1): an unquoted ID list with spaces stays one column, as on main. Meets
(2): comma and tab, quoted or unquoted, and R's default quoted space
layout all read. Does not read R's `quote=FALSE, sep=" "` one-column
sheet. That one fails loudly (IDs `S1 a` match no counts column), as it
did before #136.

**C. Drop space from the data-line sniff entirely.** Simplest. Also
gives up R's default quoted space layout (`"condition"` / `"S1" "a"`),
the most common R output after the comma form. Weaker than B on (2).

## Decision

Recommended (reviewer, not accepted): **B**. It keeps the #136 fix for
every layout R writes by default. It removes the silent drop of a sample
from an unquoted ID list. The only layout it gives up is ambiguous anyway
and fails loudly. The agreement check (ii) also stops a single odd first
row from setting the delimiter for the whole file.

## Consequences

- #136's acceptance line "the table is one column only when that line has
  none either" is narrowed: space on an unquoted data line, or rows that
  do not agree, also mean one column. The CHANGELOG entry says which.
- Tests to add: an unquoted list `sample` / `ctrl 1` / `S2` / `S3` stays
  one column through `read_delimited`, `read_id_table` and
  `detk-util tidy -p` (keeping `ctrl 1`); the same with every ID spaced;
  R's quoted space layout `"condition"` / `"S1" "a"` reads as two columns.
- Revisit if users report `quote=FALSE, sep=" "` sheets from R.
