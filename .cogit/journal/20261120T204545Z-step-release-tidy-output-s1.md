---
kind: step
time: 2026-11-20T20:45:45Z
by: DETK/developer
node: release/tidy-output
step: s1
branch: node/114-tidy-output
verdict: done
commits: [b3044fe, 61ebc1c, 4a5d046, 1443bca]
decisions: [DETK-0230]
---

# Done: Write the tidied column data as read (header, columns, no added counts column) for tidy -p and tidy-covs; make tidy, tidy-counts and tidy-covs record in the report and the crate; switch docs/tutorials/quantifiers.md to tidy -p and show tidy in its crate; tests for each; CHANGELOG; open the PR

## Summary

Done: tidy -p and tidy-covs write the sheet as read; tidy, tidy-counts, tidy-covs record in the report and crate; quantifiers tutorial on tidy -p with tidy in the crate; tests; CHANGELOG; PR

util.py: a Tidy module (names tidy, tidycounts, tidycovs) matches samples through CountMatrix as before and keeps the sheet's own columns, order, index name and values (read once as text, so 1.50 and empty cells stay as written; no added counts column; an own counts column kept). Each subcommand records with in_file_paths [counts, sheet] and out_file_paths [-o, and -p for tidy]; column_data_path is the sheet. crate.py maps the three to detk-util subcommands. Counts output unchanged (tests pin it). Decisions within the node: params are empty (the module id hashes name, params and the counts path, as for other modules with column data); each input is read once (tidy-counts/covs used to read both files twice). Proposed DETK-0230: a util-family report view for the tidy cards (report_specs.py, outside scope), carried in its own commit. tests/util/test_util.py's tidy tests now run in a temp cwd since tidy writes ./detk_report.

## Artifacts

## Findings

## Questions

- DETK-0230 detk-util tidy's report cards get a util-family view (report_specs.py, outside release/tidy-output's scope) (#118)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
