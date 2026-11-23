---
kind: task
objective: detk-util tidy's sample-sheet reader passes the sheet's name to _sniff, so a ragged sheet read through a FIFO or a process substitution is named by its path in the error, not <stream> (#149 review)
acceptance:
  - read_column_data in util.py takes the source's name before _rewindable and passes it to _sniff (name=), as read_delimited and read_id_table do; detk-util tidy -p out.csv with counts.csv and the ragged sheet condition / S1,a / S2 / S3 written to a FIFO (os.mkfifo in tmp_path) exits 1 with a message naming the FIFO's path and not <stream>; a test in tests/util/test_tidy.py
  - a ragged sheet given as a regular file is still named by its path, and every existing case in tests/util/test_tidy.py passes unchanged; CHANGELOG under Fixed
scope: [+de_toolkit/util.py, +tests/util/test_tidy.py, +CHANGELOG]
---

# detk-util tidy names a ragged sheet by the path it was given

## Implementation plan

## Notes
