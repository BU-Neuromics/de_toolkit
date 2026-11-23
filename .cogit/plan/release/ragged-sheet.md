---
kind: task
objective: A table whose header has one field and whose data lines split unalike on a delimiter (header 'condition', rows 'S1,a' and 'S2') stops with an error naming the file and the lines, instead of reading as one column that detk-util tidy then silently drops samples from (Adam, 2026-11-22; amends DETK-0320's 'else one column' for such tables)
acceptance:
  - read_delimited and read_id_table raise an error (exit 1 through any detk command, message naming the file, the delimiter and the first two lines whose field counts differ, with their counts) when the header has none of SNIFF_DELIMITERS and any of the first data lines (up to _SNIFF_DATA_LINES) splits outside quotes on a delimiter that counts under DETK-0320 (not space, or space with the line's first field quoted) while the lines do not all split alike; tests in tests/common/test_read_delimited.py for 'condition' / 'S1,a' / 'S2', for 'condition' / 'S1' / 'S2,a' (the delimiter in a later line), for the tab-separated form and for quoted R space rows that split unalike ('"condition"' / '"S1" "a"' / '"S2"')
  - 'what DETK-0320 keeps one column still reads as one column with no error and no warning: a bare ID list, quoted IDs holding a comma (''"gene_id"'' / ''"S1,a"'' / ''"S2"''), unquoted IDs with spaces anywhere in the list (''sample'' / ''ctrl 1'' / ''S2''), a header-only file; R''s one-column layouts of release/short-header (comma, tab, quoted space) still read as condition; every existing case in tests/common/test_read_delimited.py and tests/util/test_tidy.py passes unchanged'
  - detk-util tidy -p out.csv with counts 'gene,S1,S2,S3' and the sheet 'condition' / 'S1,a' / 'S2' / 'S3' exits 1 with that message on one line and writes neither the counts output nor out.csv (today it exits 0 and drops S1, logging only at INFO); a test in tests/util/test_tidy.py; read_delimited's and _sniff's docstrings say when the error is raised; CHANGELOG under Fixed
from: [DETK-0320]
scope: [+de_toolkit/common.py, +tests/common/test_read_delimited.py, +tests/util/test_tidy.py, +CHANGELOG]
issue: 145
visited: 501927d
prev: [DETK-0450]
---

# A sample sheet with ragged rows is an error, not one column

## Implementation plan

- [x] @developer When a one-field header sits over data lines that split unalike on a delimiter that counts under DETK-0320, raise an error naming the file, the delimiter and the lines; tests for the ragged forms and for what stays one column, through read_delimited, read_id_table and detk-util tidy; docstrings; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: run detk-util tidy -p on the ragged sheet and on a bare ID list, a quoted ID list with a comma and an unquoted list with spaces, and read the outputs and messages <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-22 from the release/short-header review (#138, not
blocking). Reproduced on main at d201819: counts `gene,S1,S2,S3` and the
sheet `condition` / `S1,a` / `S2` / `S3`: `detk-util tidy -p out.csv`
exits 0 and writes counts and column data for S2 and S3 only. The sheet
reads as one column (`_sniff` in `common.py`: the first data lines split
unalike, so DETK-0320 Option B says one column), its values `S1,a`, `S2`,
`S3`, so S1 matches no counts column and is dropped; the only sign is an
INFO line. With two samples the same sheet fails loudly but confusingly
("No sample names were found to be in common").

Adam asked (2026-11-22) for an error or a visible warning, as soon as
possible. Chosen: an error (within DETK-0063, no decision record): the
input is malformed, a warning on stderr is easy to miss in a pipeline,
and release/parse-errors' rule for 1.0 is that malformed input is never
silent. It narrows DETK-0320's "else one column" to lines that split on
no delimiter that counts; the space cases DETK-0320 keeps one column
(unquoted IDs with spaces) are untouched, so no new decision is needed.

Highest priority: no prev, ready now. No unfinished node holds
`common.py`, `tests/common/` or `tests/util/test_tidy.py`;
release/example-paths and release/recipe-notes (in progress) share only
the `+CHANGELOG` entry. Before release/cli-docs and release/cut.
