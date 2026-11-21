---
kind: step
time: 2026-11-20T21:45:43Z
by: DETK/developer
node: release/cli-messages
step: s1
branch: node/124-cli-messages
verdict: done
commits: [775e4ed, 0976e4d, 66ea2a0, 90f4dd8, 31f35e9, e217d1c]
decisions: []
---

# Done: Say 'Invalid design: <reason>' for designs that parsed but could not be built, quiet ply.yacc's table and conflict output in detk-filter (pinning the conflict count), read a design beginning with '-' as the design; tests and cli-pin rows; CHANGELOG; open the PR

## Summary

'Invalid design: <reason>' for designs that parsed but could not be built (syntax failures say 'could not read the design'); detk-filter builds its ply parser once, in memory and quiet, with the 4 shift/reduce conflicts and today's and/or grouping pinned by tests (DETK-0270 Proposed: whether to change the grouping for 1.0); a word starting with - holding ~ or a space that is no option of the parser is a positional, so '-2.5 ~ counts' reaches DETK-0190's message in detk-de deseq2/firth and detk-transform rlog; tests, cli-pin rows, CHANGELOG

## Artifacts

## Findings

## Questions
