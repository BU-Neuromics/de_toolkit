---
kind: step
time: 2026-11-09T19:51:33Z
by: DETK/developer
node: release/escape-json
step: s1
branch: node/46-escape-json
verdict: done
commits: [74ecf08, 978022b]
decisions: [DETK-0014]
---

# Done: Fix it with tests and a CHANGELOG entry; open the PR

## Summary

Module JSON embedded in the report's script elements is now serialized by report.script_json, which escapes <, >, & and U+2028/2029 as \uXXXX, so no user string can end the block; NumpyEncoder now JSON-encodes object keys. tests/report/test_report_escape.py renders a report with </script><script>alert(1)</script> in sample names, column values, size-factor keys and annotate fields and checks the script elements are intact and the data round-trips (fails on main, passes here). CHANGELOG Fixed entry. pytest 219 passed/49 skipped, ruff check and format clean, mkdocs --strict builds. DETK-0014 records that view text inserted with innerHTML (filtercounts note, raw-fallback error) is a remaining path outside this node's scope.

## Artifacts

## Findings

## Questions
