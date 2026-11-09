---
kind: task
objective: 'Zero-padded feature IDs survive the shared counts reader: 007 stays 007 and matches other files (tracks #48)'
acceptance:
  - the counts reader reads the ID column as text; 007 is kept in every tool's output and matches a lengths or mapping file, with tests
  - docs/tools/norm.md's sentence on numeric IDs holds for zero-padded IDs
scope: [de_toolkit/common.py, tests/common/, docs/tools/norm.md, +CHANGELOG]
---

# Read feature IDs as text

## Implementation plan

- [ ] @developer Fix it with tests and a CHANGELOG entry; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.
