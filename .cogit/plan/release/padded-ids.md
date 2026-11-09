---
kind: task
objective: 'Zero-padded feature IDs survive the shared counts reader: 007 stays 007 and matches other files (tracks #48)'
acceptance:
  - the counts reader reads the ID column as text; 007 is kept in the output of every command that reads counts in Python and matches a lengths or mapping file, with tests (the R-backed commands, fgsea and tidy-counts/tidy-covs are release/r-ids, DETK-0015)
  - docs/tools/norm.md's sentence on numeric IDs holds for zero-padded IDs
scope: [de_toolkit/common.py, tests/common/, docs/tools/norm.md, +CHANGELOG]
issue: 48
visited: b94644c
prev: [DETK-0015]
---

# Read feature IDs as text

## Implementation plan

- [x] @developer Fix it with tests and a CHANGELOG entry; open the PR <!-- s1 -->
- [x] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.
