---
kind: task
objective: detk-util tidy -p and tidy-covs write the column data with the input's header and columns only, and tidy, tidy-counts and tidy-covs record in the report and the Process Run Crate like the other steps
acceptance:
  - 'detk-util tidy -p FILE and detk-util tidy-covs write the tidied column data with exactly the input file''s columns, in its order, under its header: the first header cell is the input''s (e.g. sample, so the header is sample,condition and not ,condition,counts), and no counts column of zeros is added (the one CountMatrix adds internally); a column data file that has its own counts column keeps it with its values; tests in tests/util/ compare the written header and rows to the input''s for tidy -p and tidy-covs, the counts output of tidy and tidy-counts unchanged'
  - 'detk-util tidy, tidy-counts and tidy-covs write to the report unless --no-report, as gather and annotate do: a module entry naming the subcommand, both input files and the output, and for tidy the -p output when given (through the optional in_file_paths and out_file_paths that release/record adds to the envelope); the Process Run Crate (ro-crate-metadata.json) then lists the tidy step with its inputs and outputs; a test runs tidy -p into a report dir and checks the module JSON and the crate, and one checks --no-report writes no report; their help''s --report-dir/--no-report now describe what happens'
  - docs/tutorials/quantifiers.md (release/tutorial-quant) uses detk-util tidy -p for the sample sheet to write the tidied sample sheet and uses it downstream, in place of its workaround (tidy without -p, then the original sheet), and lists tidy among the crate's steps, with the page's checked step count updated; the tutorial runs green under the tutorial harness; CHANGELOG under Fixed
scope: [+de_toolkit/util.py, +de_toolkit/crate.py, tests/util/, +tests/cli/cli_cases.py, +tests/cli/cli_tables.py, +docs/tutorials/quantifiers.md, tests/tutorials/, +CHANGELOG]
prev: [release/record, release/tutorial-quant, DETK-0230]
issue: 114
visited: 118283e
---

# detk-util tidy writes the sample sheet as read and records in the report

## Implementation plan

- [x] @developer Write the tidied column data as read (header, columns, no added counts column) for tidy -p and tidy-covs; make tidy, tidy-counts and tidy-covs record in the report and the crate; switch docs/tutorials/quantifiers.md to tidy -p and show tidy in its crate; tests for each; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: run tidy -p on a real sample sheet and read the file, check the module JSON and the crate, run the quantifiers tutorial <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 from bugs found by node sessions and reviewers. Two
bugs, one module:

- The `counts` column of zeros comes from `CountMatrix`
  (`de_toolkit/common.py`, where a column data frame without one gets
  `column_data["counts"] = 0` for the design machinery); `tidy -p` and
  `tidy-covs` write `count_obj.column_data` as it is, with `to_csv` and no
  index label, so the header loses `sample` and gains `counts`. The fix
  belongs at the write in `util.py`; `common.py` stays as it is (other
  commands rely on the column).
- `detk-util tidy*` never write to the report, yet their help lists
  `--report-dir`/`--no-report` (shared command options), so they are
  missing from the report and the Process Run Crate. Recording them like
  gather and annotate is the help's promise and what the crate needs to
  trace a tidied file to its inputs; no decision needed.

After release/record, which edits `util.py`, `crate.py`, `report.py` and
`tests/util/` and adds the envelope's multi-file fields used here, and
after release/tutorial-quant (PR #103), whose page this node changes from
its workaround to `tidy -p`. Before release/cli-docs and release/cut.
