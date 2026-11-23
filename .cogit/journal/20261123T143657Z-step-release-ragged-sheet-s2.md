---
kind: step
time: 2026-11-23T14:36:57Z
by: DETK/reviewer
node: release/ragged-sheet
step: s2
branch: review/ragged-sheet
verdict: approve
commits: [279b8b7]
decisions: []
---

# Approved: Review the PR: run detk-util tidy -p on the ragged sheet and on a bare ID list, a quoted ID list with a comma and an unquoted list with spaces, and read the outputs and messages

## Summary

Approved (re-recorded after DETK-0450 was accepted): the ragged sheet stops tidy with exit 1 and a one-line message naming the file, delimiter and lines, and writes nothing; the bare, quoted-comma and spaced ID lists still read as one column with no warning; CI green including the R job; the replaced test was right; DETK-0450 records the DETK-0320 amendment

## Artifacts

## Findings

Checks: CI green on 432c313, every job, including test with R (bioconda) (23m56s), docs build (strict), ruff and coverage. Locally (uv, Python 3.13, no R) the full suite passes: 2509 passed, 142 skipped.

detk-util tidy --no-report -o c.csv -p out.csv, counts gene,S1,S2,S3:
- ragged sheet condition / S1,a / S2 / S3: exit 1, one stderr line `detk-util: error: ragged.csv: the header 'condition' has one field and its data lines split unalike on comma: line 2 'S1,a' has 2 fields, line 3 'S2' has 1 field; quote a field that holds the delimiter, or give every line the same fields (--verbose for the traceback)`; neither c.csv nor out.csv written.
- later line (condition / S1 / S2,a / S3), tab form, .gz, /dev/stdin: the same error with the right delimiter and name.
- bare IDs (sample / S1 / S2 / S3): exit 0, all three kept, no warning.
- quoted IDs with a comma ("sample" / "S1" / "S2,x" / "S3", counts holding "S2,x"): exit 0, one column, 0 lost, no warning; out.csv re-quotes "S2,x".
- unquoted IDs with spaces (sample / S1 / ctrl 1 / S3, counts holding ctrl 1): exit 0, one column, 0 lost, no warning.
- R one-column layout ("condition" / "S1","a" ...): reads as condition, as before.

Replaced test: test_data_lines_that_split_unalike_mean_one_column asserted the exact reading the objective removes (its first case is the objective's own example), so it could not pass unchanged. "Every existing case passes unchanged" contradicts the objective for that one test, and replacing it is right. Both of its inputs are covered by the new error tests ('comma' and 'three fields'). Every other existing case is unchanged and passes.

DETK-0320: its Option B (ii) and Consequences say lines that do not agree mean one column. This PR reverses that for delimiters that count, so the Accepted record now describes a rule the code no longer follows. I recorded DETK-0450 (Proposed, #152), recommending Adam accept it and revise DETK-0320 to point to it. Not blocking the merge.

Non-blocking, not asked here:
1. Line numbers in the message count non-blank lines, so a blank line within the first 11 lines after skiprows makes them off by one (condition / (blank) / S1,a / S2 reports lines 2 and 3, really 3 and 4). The quoted line text still finds the lines, the case is rare, and fixing it means tracking raw line numbers through _first_lines' pandas read. Leave it as a known limit (written into DETK-0450's Consequences), or fix in a follow-up, not here.
2. tidy's sheet reader (util.py, _read_column_data) calls _sniff after _rewindable without name=, so a ragged sheet given through a process substitution (<(cat s.csv)) is named `<stream>` rather than /dev/fd/NN. read_delimited and read_id_table capture the name first. util.py is outside the node's scope, and the name /dev/fd/NN would say little anyway. A one-line follow-up if wanted.

## Questions
