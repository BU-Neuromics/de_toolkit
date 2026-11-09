---
kind: task
objective: 'report: the module JSON is embedded in the report''s script block escaped, so no string in it can end the block (tracks #46)'
acceptance:
  - a feature ID, sample name or annotation value containing </script> leaves the report intact, with a test
scope: [de_toolkit/templates/report.html, de_toolkit/report.py, tests/report/, +CHANGELOG]
issue: 46
visited: b94644c
---

# Escape the module JSON in the report

## Implementation plan

- [ ] @developer Fix it with tests and a CHANGELOG entry; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.
