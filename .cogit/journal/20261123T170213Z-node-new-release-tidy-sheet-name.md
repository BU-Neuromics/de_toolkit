---
kind: action
time: 2026-11-23T17:02:13Z
by: adamlabadorf
action: node-new
node: release/tidy-sheet-name
---

# New node release/tidy-sheet-name

Task release/tidy-sheet-name: detk-util tidy's sample-sheet reader passes the sheet's name to _sniff, so a ragged sheet read through a FIFO or a process substitution is named by its path in the error, not <stream> (#149 review)
