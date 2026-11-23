---
kind: task
objective: detk-util tidy's sample-sheet reader passes the sheet's name to _sniff, so a ragged sheet read through a FIFO or a process substitution is named by its path in the error, not <stream> (#149 review)
acceptance:
  - read_column_data in util.py takes the source's name before _rewindable and passes it to _sniff (name=), as read_delimited and read_id_table do; detk-util tidy -p out.csv with counts.csv and the ragged sheet condition / S1,a / S2 / S3 written to a FIFO (os.mkfifo in tmp_path) exits 1 with a message naming the FIFO's path and not <stream>; a test in tests/util/test_tidy.py
  - a ragged sheet given as a regular file is still named by its path, and every existing case in tests/util/test_tidy.py passes unchanged; CHANGELOG under Fixed
scope: [+de_toolkit/util.py, +tests/util/test_tidy.py, +CHANGELOG]
issue: 158
visited: 203b21f
status: done
done: 02da492
---

# detk-util tidy names a ragged sheet by the path it was given

## Implementation plan

- [x] @developer Pass the sheet's name to _sniff in read_column_data; a FIFO test through detk-util tidy; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: run detk-util tidy -p with the ragged sheet through <(cat sheet.csv) and as a file, and read both messages <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-23 from the release/ragged-sheet review (#149, not
blocking, item 2): `read_column_data` (util.py, about line 502) calls
`_sniff(f, compression)` after `_rewindable`, without `name=`, so for a
FIFO or process substitution, which `_rewindable` reads into a BytesIO,
the ragged-sheet error falls back to `_source_name` of the buffer and says
`<stream>`. read_delimited and read_id_table (common.py) capture
`_source_name(source)` before `_rewindable`; this does the same. A regular
file is unaffected (`_rewindable` returns the path).

Scope shares only `+` entries: release/record-program also edits util.py
(`run_record`) and its own tests/util/test_record.py, a different function
and file, so the two do not collide. Ready now; before release/cut.
