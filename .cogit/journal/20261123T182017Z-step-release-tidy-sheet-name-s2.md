---
kind: step
time: 2026-11-23T18:20:17Z
by: DETK/reviewer
node: release/tidy-sheet-name
step: s2
branch: review/tidy-sheet-name
verdict: approve
commits: [308b942]
decisions: []
---

# Approved: Review the PR: run detk-util tidy -p with the ragged sheet through <(cat sheet.csv) and as a file, and read both messages

## Summary

Approved: the ragged sheet through <(cat sheet.csv) is named /dev/fd/63 and as a file sheet.csv, exit 1 and nothing written either way; the FIFO test fails on the base with <stream> and passes here; existing tidy tests unchanged; CHANGELOG under Fixed; CI green including the R job

## Artifacts

## Findings

Checks: CI green on 308b942, every job, including test with R (bioconda) (21m40s), docs build (strict), ruff, runtime dependencies only and combined coverage. Locally (uv, Python 3.13, no R): full suite 2554 passed, 154 skipped; ruff check and format clean; tests/util/test_tidy.py 30 passed.

detk-util tidy --no-report -p out.csv, counts gene,S1,S2,S3, ragged sheet condition / S1,a / S2 / S3:
- through <(cat sheet.csv): exit 1, `detk-util: error: /dev/fd/63: the header 'condition' has one field and its data lines split unalike on comma: line 2 'S1,a' has 2 fields, line 3 'S2' has 1 field; quote a field that holds the delimiter, or give every line the same fields (--verbose for the traceback)`; no `<stream>`; out.csv not written.
- as the file sheet.csv: exit 1, the same message naming `sheet.csv`; out.csv not written.

The change: read_column_data takes _source_name(f) before _rewindable and passes it to _sniff(name=), as read_delimited (common.py:979) and read_id_table (common.py:1016) do; those are now all the _sniff calls, every one named.

The new test (os.mkfifo in tmp_path, a writer thread, through main) fails on the base 203b21f with `detk-util: error: <stream>: ...` and passes here, so it tests the fix. The test file's diff only adds lines; every existing case is unchanged and passes. CHANGELOG entry under Fixed, #158.

No decisions needed; nothing non-blocking to raise.

## Questions
