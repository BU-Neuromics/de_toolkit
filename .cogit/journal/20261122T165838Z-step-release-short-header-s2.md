---
kind: step
time: 2026-11-22T16:58:38Z
by: DETK/reviewer
node: release/short-header
step: s2
branch: review/short-header
verdict: approve
commits: [dd3f7af, fc5cccd]
decisions: []
---

# Approved: Review the PR: run detk-util tidy -p on '"condition"' over '"S1","a"' rows, and on a bare quoted ID list, and read both outputs

## Summary

Approved at d6163ab (code fc5cccd): DETK-0320 B implemented as recorded; the earlier finding is fixed (unquoted sample/ctrl 1/S2/S3 tidies keeping ctrl 1; every-spaced and later-spaced lists stay one column); R's comma, tab, quoted-space layouts read as condition; renumbering 0281->0320 clean; CI green incl. R

## Artifacts

## Findings

Re-review of the s2 findings. 1. Fixed: _sniff takes the data line's delimiter only if it is not space or the line's first field is quoted, and the first 10 data lines split alike into >= 2 fields. Reproduced: tidy -p on counts gene,ctrl 1,S2,S3 + unquoted sample/ctrl 1/S2/S3 keeps all 3 samples and writes sample/ctrl 1/S2/S3 (b18d918 dropped ctrl 1); sample/sample 1/sample 2 reads as IDs sample 1, sample 2 and tidies; later-spaced list stays one column. #136 fix intact: tidy -p on '"condition"'/'"S1","a"' writes ,condition/S1,a/S2,b; R default '"condition"'/'"S1" "a"' reads as condition; bare quoted ID list stays one column. Extra edge cases OK: unquoted comma rows with spaces in values (S1,ctrl a), quoted values with spaces, tab rows with spaces, CRLF, no trailing newline, blank line after header, gene_id list. R quote=FALSE sep=' ' stays one column, as DETK-0320 accepts and the CHANGELOG says. 2. Tests cover every case asked (read_delimited, read_id_table, tidy -p), plus unalike rows and >10 rows. 3. Renumbering: no stray DETK-0281 on the branch; the only 0281 is the stop note describing the rename; record, journal entries and node prev name DETK-0320. 4. Local tests/common+tests/util 248 passed, 1 skipped; ruff check/format clean; CI on d6163ab all green incl. 'test with R (bioconda)' and combined coverage. Nit, not blocking and as on main: a malformed ragged sheet (condition / S1,a / S2) reads as one column, so tidy can drop S1 with only an INFO line.

## Questions
