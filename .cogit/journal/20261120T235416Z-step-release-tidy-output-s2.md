---
kind: step
time: 2026-11-20T23:54:16Z
by: DETK/reviewer
node: release/tidy-output
step: s2
branch: review/tidy-output
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: run tidy -p on a real sample sheet and read the file, check the module JSON and the crate, run the quantifiers tutorial

## Summary

Approved at 5bd350e: the short-header fix reads every field as text and tells the layout by field counts, so 001/002 and 1/3 IDs now match and round-trip; all earlier round-trip, report and crate checks still hold; tests added; CI green incl. R

## Artifacts

## Findings

Re-review of PR #119 at 5bd350e (branch tip 9a83c60, a stop note only), against the s2 findings in dedc94d. Approved.

Change asked 1 (short-header sheet with numeric-looking IDs): fixed
- read_column_data now reads every line as text fields with header=None and dtype=str, and tells the layout from the header's field count against the first row's: equal means the first cell names the IDs (empty becomes unnamed), one fewer means R's write.table layout. Anything else is a clear error. pandas types nothing, so 001 stays 001.
- My earlier repro, counts `gene,001,002,S3,P1` with sheet `"condition","dose"` / `"001","ctrl","1.50"` / `"002","treat",""`, now gives counts `gene,001,002` and -p `,condition,dose / 001,ctrl,1.50 / 002,treat,`. IDs 1/3 against counts `1,3,7` work too (that case failed on main).
- Re-ran every earlier case, and each round-trips exactly: the named header (`sample,...`, with 0.10, 1.50, 07, empty cells and a quoted comma), R write.csv's empty first cell, duplicate rows as on main, and a TSV sheet. A ragged short row gets an empty cell, and a blank line is skipped. Module JSON with a short-header sheet: in_file_paths [counts, sheet], out_file_paths [-o, -p], num_samples 2.
- New tests: a short-header sheet with ids 001/002 and 1/3, checking both outputs; a header neither as long as nor one shorter than the first row exits with an error.

Checks
- CI green on 5bd350e in all 11 jobs, including test with R (bioconda). Locally (3.13, no R): 2249 passed, 92 skipped, the quantifiers tutorial among them.

Not blocking (unchanged from the first review; pre-existing, outside scope)
- A one-column sheet with a quoted header fails in the delimiter sniffing.
- The crate is written to the working directory whatever --report-dir is.

## Questions
