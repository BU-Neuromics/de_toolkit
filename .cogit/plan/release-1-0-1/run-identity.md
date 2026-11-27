---
kind: task
objective: a module record's identity includes every input and output path, so runs with the same parameters on different files are not collapsed into one record
acceptance:
  - 'reproduced first as a test: on v1.0.0 ''detk-filter -o a.csv EXPR counts.csv'' then ''-o b.csv'' with the same expression leave one module JSON, naming b.csv only; likewise two detk-de deseq2 runs differing only in the sample information file, and two fgsea runs differing only in the results file. After: two records each, both in the crate'
  - re-running an identical command (same parameters, inputs and outputs) still replaces its one record
  - docs/report.md says what identifies a record; CHANGELOG 1.0.1 entry
scope: [de_toolkit/report.py, tests/report/, +docs/report.md, +CHANGELOG]
issue: 182
visited: 557da83
---

# Runs that differ only in their files keep separate records

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; it reproduced: two detk-filter runs
with the same expression and -o a.csv, -o b.csv leave one module JSON naming
b.csv; a detk-de deseq2 run on a mismatched sample sheet and one on the
right sheet, and fgsea runs differing only in -c, also collapsed into one
record each. The identity is `hash(name + params + in_file_path + version)`
(de_toolkit/report.py, about line 312): only the primary input. Adding every
input and output path (relative, as recorded) changes record ids, which is
fine: ids already change with the version.
