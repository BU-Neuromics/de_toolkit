---
kind: task
objective: the fgsea crate action lists the DE results file as an input beside the GMT file, so the enrichment table links to the DE step that wrote its ranking
acceptance:
  - 'reproduced first as a test: on v1.0.0 the crate action of ''detk-enrich fgsea -c ... gene_sets.gmt de.csv'' has object gene_sets.gmt and the params but not de.csv, though argv names it. After: object holds both files (in_file_paths), and the module JSON''s in_file_path stays the GMT'
  - CHANGELOG 1.0.1 entry
scope: [de_toolkit/enrich.py, tests/enrich/, tests/report/, +CHANGELOG]
prev: [release-1-0-1/fgsea-statcol]
issue: 199
visited: ff47136
---

# fgsea records the results file it ranked as an input

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; it reproduced:
the crate action's object is `../gene_sets.gmt` plus the params, with no
`../de.csv`. `enrich.py` calls `add_module(in_file_path=args.gmt_fn, ...)`
only; pass `in_file_paths=[gmt_fn, result_fn]` as `detk-util tidy` and
`record` do. After fgsea-statcol, which edits the same file.
