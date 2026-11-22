---
kind: task
objective: A table whose header has one field and whose rows have more (R's write.table layout with one column, e.g. "condition" over "S1","a") is read with the rows' delimiter, not taken for a one-column table
acceptance:
  - read_delimited reads a sheet '"condition"' / '"S1","a"' / '"S2","b"' as sample IDs S1 and S2 with one column condition, today an error ('' expected after '"') from the one-column path; the same with an unquoted header, with tab-separated rows, and with IDs 001/002 kept as written; when the first line has none of SNIFF_DELIMITERS the delimiter is sniffed from the first data line, and the table is one column only when that line has none either
  - 'a real one-column table still reads as one column: a quoted header over quoted IDs (''"gene_id"'' / ''"ENSG1"''), an unquoted one, and a header-only file; the existing tests/common/test_read_delimited.py cases pass unchanged'
  - detk-util tidy -p with the sheet '"condition"' / '"S1","a"' against counts 'gene,S1,S2' succeeds and writes the sheet with its condition column, and a detk command that reads column data (detk-de or detk-filter on a design over condition) reads it; tests in tests/common/ and tests/util/test_tidy.py; CHANGELOG under Fixed
scope: [+de_toolkit/common.py, +de_toolkit/util.py, +tests/common/test_read_delimited.py, +tests/util/test_tidy.py, +CHANGELOG]
prev: [release/cli-messages, DETK-0320]
issue: 136
visited: 06c6a10
status: done
done: b8a736e
---

# A one-field header over wider rows reads as R writes it

## Implementation plan

- [x] @developer When the first line has no delimiter, sniff the first data line before reading the table as one column; tests for the short one-field header (quoted, unquoted, tab, padded IDs) and for real one-column tables, through read_delimited, detk-util tidy and a command that reads column data; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: run detk-util tidy -p on '"condition"' over '"S1","a"' rows, and on a bare quoted ID list, and read both outputs <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-21 from the release/tidy-output review (#119, not
blocking). Reproduced on main at 61bf890: counts `gene,S1,S2` and the sheet
`"condition"` / `"S1","a"` / `"S2","b"` give `detk-util: error: '' expected
after '"'`. `sniff_delimiter` (`common.py`, about line 776) sees no
delimiter in the header `"condition"`, returns None, and the table is read
as one column with `\x1f` as separator, where the quoted, comma-separated
rows break the parser. This is R's `write.table(sep=",")` layout (no header
cell over the row names) with a single column; release/tidy-output taught
`read_column_data` that layout for wider sheets, but the sniff runs first.
DETK-0020 (a first line with none of the fixed delimiters is one column)
was written for bare ID lists; looking at the next line keeps that for
them, so no decision is needed (within DETK-0063).

After release/cli-messages (#127, in progress), which edits `common.py`
and holds `tests/common/`. Before release/cut.
