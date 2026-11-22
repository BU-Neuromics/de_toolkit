---
kind: step
time: 2026-11-22T18:17:04Z
by: DETK/developer
node: release/ragged-sheet
step: s1
branch: node/145-ragged-sheet
verdict: done
commits: [aae8bdf]
decisions: []
---

# Done: When a one-field header sits over data lines that split unalike on a delimiter that counts under DETK-0320, raise an error naming the file, the delimiter and the lines; tests for the ragged forms and for what stays one column, through read_delimited, read_id_table and detk-util tidy; docstrings; CHANGELOG; open the PR

## Summary

RaggedTableError in _sniff for a one-field header over data lines that split unalike on a delimiter that counts under DETK-0320; message names the file, delimiter, first two differing lines and their field counts; tests in test_read_delimited.py (comma, later line, tab, quoted space, three fields, stream, skiprows; what stays one column with no warning) and test_tidy.py (exit 1, one line, no outputs); docstrings; CHANGELOG Fixed. Note: test_data_lines_that_split_unalike_mean_one_column asserted the removed behaviour and is replaced by the error tests, against the acceptance's 'every existing case passes unchanged'.

## Artifacts

## Findings

## Questions
