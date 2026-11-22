---
kind: step
time: 2026-11-22T15:40:01Z
by: DETK/developer
node: release/short-header
step: s1
branch: node/136-short-header
verdict: done
commits: [b7d713d]
decisions: []
---

# Done: When the first line has no delimiter, sniff the first data line before reading the table as one column; tests for the short one-field header (quoted, unquoted, tab, padded IDs) and for real one-column tables, through read_delimited, detk-util tidy and a command that reads column data; CHANGELOG; open the PR

## Summary

When a table's first line has none of SNIFF_DELIMITERS, the delimiter is sniffed from its first data line (counting only when it splits that line outside quotes), shared by read_delimited, read_id_table and read_column_data via common._sniff; '"condition"' over '"S1","a"' now reads as IDs S1,S2 with column condition (quoted, unquoted, tab, padded 001/002), real one-column tables (quoted, unquoted, quoted IDs with spaces, header-only) stay one column; tests through read_delimited, read_id_table, detk-util tidy -p and detk-filter; CHANGELOG under Fixed

## Artifacts

## Findings

## Questions
