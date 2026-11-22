---
kind: step
time: 2026-11-22T15:40:06Z
by: DETK/developer
node: release/record-help
step: s1
branch: node/135-record-help
verdict: done
commits: [a5a60ed]
decisions: []
---

# Done: Reword record's --tool-version sentence, drop -d/--out-delim from detk-util record (kept on every other command), the same in docs/tools/util.md and the skill's commands page; help tests and cli-pin rows; CHANGELOG; open the PR

## Summary

record's --tool-version sentence reworded; -d/--out-delim dropped from detk-util record only (add_common_options(out_delim=False)); docs/tools/util.md, skills commands page, cli tables (Sub.without_common), help tests, CHANGELOG. Also regenerated de_toolkit/completions/detk.{bash,zsh} (outside the listed scope; tests/completion requires them to match the parsers).

## Artifacts

## Findings

## Questions
