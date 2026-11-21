---
kind: action
time: 2026-11-21T01:18:17Z
by: adamlabadorf
action: node-new
node: release/report-paths
---

# New node release/report-paths

Task release/report-paths: Each report directory holds its own Process Run Crate, and the paths recorded in module JSON and the crate are relative to the report directory, so no absolute machine path is written for a run given relative paths (DETK-0280; Adam, 2026-11-20) Plan copied from release/record-help.
