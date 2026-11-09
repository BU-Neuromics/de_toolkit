---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/single-column, step: s1}
applies: [release/single-column]
allowed_by: [reasonable]
reason: csv.Sniffer left to any character splits a bare list of IDs on a letter of its header
---

# Sniff delimiters from a fixed set; a first line with none is one column

## Background

detk reads most of its inputs (counts and column-data files, the result
and mapping tables of `detk-util annotate`, the files of `tidy-counts` and
`tidy-covs`, the result table of `detk-enrich fgsea`) without being told
their delimiter: pandas' `sep=None` hands the first line to Python's
`csv.Sniffer`, which guesses one. The sniffer may pick any character, so
for a file with one column, such as a bare list of gene IDs, it picked a
letter of the header: `id` was read with the header `,d`, `gene_id` as
`g`, `n`, `_id`, and the run went on and exited 0 (#47).

## Context

A bare list of IDs is a plausible input (a gene list to annotate, a
sample sheet that only names samples). The fix must tell "this line has no
delimiter" from "this line is split on X", keep every comma, tab and
semicolon file reading as before, and keep `read_id_table`'s handling of
streams, FIFOs, compressed files and URLs (#48). The rule is shared by
every reader, so later work (the R-ID node touching `enrich.py` and
`util.py`, any new reader) inherits it.

## Options

1. **Sniff only for a fixed set of delimiters (comma, tab, semicolon,
   pipe, space); a first line with none of them is one column.** Simple to
   state and to document; also stops a one-column file of versioned IDs
   (`ENSG01.5`) being split on `.`, or one with a header like `gene-id` on
   `-`. Gives up any other delimiter the sniffer could find before (`:`,
   or any letter), which no tabular format detk reads uses.
2. **Let the sniffer pick any character, and fall back to one column when
   it picks a letter or digit.** Smallest change in behaviour, but still
   splits on punctuation in an ID (`.`, `-`, `_` is a word character but
   `.` is not), so `ENSG01.5` as a header would still be split.
3. **Sniff over several lines rather than the first.** More evidence, but
   the sniffer's consistency test fails on the R-style counts header that
   omits the index column's field (one field fewer than the data lines),
   which detk must read.

## Decision

Option 1: `de_toolkit.common.read_delimited` (and `sniff_delimiter`)
sniff the first line, as pandas did, for `SNIFF_DELIMITERS = ",\t;| "`;
with none of them the file is read as a single column. Every reader that
used `sep=None` in common, util and enrich goes through it. Space stays
in the set so whitespace-separated tables still read; comma, tab and
semicolon are preferred over it, as the sniffer's own preference order
has them.

## Consequences

- A one-column file reads as one column everywhere it is sniffed, with
  tests for `id` and `gene_id`, with and without a header.
- A one-column file whose first line contains a space (a header such as
  `gene id`) is read as two columns; a table delimited by any character
  outside the set (`:`) is read as one column. Revisit if a user reports
  either.
- New readers should call `read_delimited` instead of `sep=None`.
  `de_toolkit/norm.py`'s `read_lengths` still uses `sep=None` (outside this
  node's scope); a lengths file must have two columns, so a one-column file
  there still fails, but with a wrong column count rather than one column.
- The first line is read once more before the table: a URL is fetched
  twice; a stream or FIFO is buffered first, as `read_id_table` already did.
