---
kind: task
objective: a module record's identity includes every input and output path, so runs with the same parameters on different files are not collapsed into one record
acceptance:
  - 'reproduced first as a test: on v1.0.0 ''detk-filter -o a.csv EXPR counts.csv'' then ''-o b.csv'' with the same expression leave one module JSON, naming b.csv only; likewise two detk-de deseq2 runs differing only in the sample information file, and two fgsea runs differing only in the results file. After: two records each, both in the crate'
  - re-running an identical command (same parameters, inputs and outputs) still replaces its one record
  - docs/report.md says what identifies a record; CHANGELOG 1.0.1 entry
scope: [de_toolkit/report.py, +tests/report/, +docs/report.md, +CHANGELOG]
---

# Runs that differ only in their files keep separate records

## Implementation plan

## Notes
