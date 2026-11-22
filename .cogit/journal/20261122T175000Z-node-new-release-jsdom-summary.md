---
kind: action
time: 2026-11-22T17:50:00Z
by: adamlabadorf
action: node-new
node: release/jsdom-summary
---

# New node release/jsdom-summary

Task release/jsdom-summary: The 'Report render tests ran in jsdom' CI step decides pass or fail from pytest's final summary line alone, so a passing test whose name holds 'error' or 'failed' cannot fail CI, and test_report_view_text.py's imports are in order
