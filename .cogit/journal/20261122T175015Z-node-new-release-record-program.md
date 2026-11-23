---
kind: action
time: 2026-11-22T17:50:15Z
by: adamlabadorf
action: node-new
node: release/record-program
---

# New node release/record-program

Task release/record-program: As DETK-0390 is answered (recommended Option B): detk-util record writes the program of the step it records, typed as an absolute path, as its bare name when PATH finds that same file by that name, as detk's own argv[0] is its name, instead of a ../ chain whose depth is the working directory's
