---
kind: step
time: 2026-11-22T16:08:31Z
by: DETK/reviewer
node: release/short-header
step: s2
branch: review/short-header
verdict: changes
commits: [3c96e77]
decisions: [DETK-0281]
---

# Changes asked: Review the PR: run detk-util tidy -p on '"condition"' over '"S1","a"' rows, and on a bare quoted ID list, and read both outputs

## Summary

Changes asked at b18d918: the data-line sniff silently mis-splits an unquoted one-column ID list whose first ID has a space (tidy drops that sample, exit 0); DETK-0281 Proposed (recommend B: space from the data line only outside quoted fields, and the first data lines must agree on a field count >= 2). The #136 fix itself works: tidy -p on '"condition"' over '"S1","a"' writes ,condition/S1,a/S2,b; a bare quoted ID list stays one column. CI green incl. R

## Artifacts

## Findings

1. (blocking, regression) Counts gene,ctrl 1,S2,S3 with column data sample / ctrl 1 / S2 / S3 (unquoted, as Excel exports it). main 06c6a10: tidy keeps all 3 samples. PR b18d918: read as IDs ctrl,S2,S3 with a column sample = 1,NaN,NaN (pandas fills the ragged rows, no error); detk-util tidy -p exits 0, drops ctrl 1 from the counts (only an INFO 'counts columns lost: 1') and writes a made-up sample column. Silent wrong result. With every ID spaced (sample / sample 1 / sample 2) IDs become sample,sample and tidy errors 'No sample names ... in common': loud but a regression from main. If the spaced ID is on a later line it stays one column: the result depends on row order. Choice recorded as DETK-0281 (Proposed); recommended B: from the data line, accept space only outside quoted fields (R's default write.table(sep=' ') quotes, so '"condition"' / '"S1" "a"' still reads), and require the first data lines to split into the same field count >= 2, else one column. Tests to add: the unquoted spaced lists above through read_delimited, read_id_table and tidy -p (ctrl 1 kept); R's quoted space layout reads as two columns. CHANGELOG entry to say which. 2. Verified OK: tidy -p on '"condition"' / '"S1","a"' / '"S2","b"' against gene,S1,S2 writes ,condition / S1,a / S2,b and counts unchanged; bare quoted ID list '"sample"' / '"S1"' / '"S2"' writes sample / S1 / S2 (one column); quoted IDs with spaces stay one column; unquoted and quoted space-separated R sheets read as condition. tests/common + tests/util: 236 passed, 1 skipped locally; ruff clean; CI all green incl. 'test with R (bioconda)'. CHANGELOG under Fixed present.

## Questions

- DETK-0281 A one-field header over unquoted space-separated rows: one column or two

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
