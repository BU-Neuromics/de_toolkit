---
kind: task
objective: 'A one-column input file is read as one column, not split on a letter of its header (tracks #47)'
acceptance:
  - a bare list of IDs reads as one column in every reader that sniffs the delimiter (common, enrich, util), with tests
scope: [de_toolkit/common.py, de_toolkit/enrich.py, de_toolkit/util.py, tests/common/, +CHANGELOG]
prev: [release/padded-ids, release/gather]
issue: 47
visited: a328c16
status: done
done: ec56f05
---

# Read single-column files

## Implementation plan

- [x] @developer Fix it with tests and a CHANGELOG entry; open the PR <!-- s1 -->
- [x] @reviewer Review the PR <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.
