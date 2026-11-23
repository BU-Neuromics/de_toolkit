---
kind: action
time: 2026-11-23T17:02:13Z
by: adamlabadorf
action: node-new
node: release/workflow-permissions
return: 38s
---

# New node release/workflow-permissions

Task release/workflow-permissions: Every job in ci.yml and release.yml runs with a GITHUB_TOKEN limited to what it needs, closing CodeQL's actions/missing-workflow-permissions alerts #1 #3 #4 #5 #7 #10 (ci.yml) and #6 (release.yml), with Trusted Publishing intact
