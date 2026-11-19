---
kind: step
time: 2026-11-19T20:36:57Z
by: DETK/developer
node: release/cli-pin
step: s1
branch: node/70-cli-pin
verdict: done
commits: [fcfaed8, e02f576]
decisions: []
---

# Done: Write `tests/cli/`: per-command tables of command lines and the arguments each yields, the invalid lines and their exits, the help facts, the named docopt behaviours and the umbrella command, through one adapter at the point each `main` dispatches; no change to `de_toolkit/`; open the PR

## Summary

tests/cli pins all 11 entry points (1,298 tests, 1 skipped for DETK-0033): per-command tables, one adapter stopping each main at dispatch, generated short/long/default lines, invalid lines, help facts per DETK-0025 B, named docopt behaviours, umbrella detk as it is, console scripts. No change to de_toolkit/. Found: --out is ambiguous with --out-delim (pinned rejected; --outp pinned accepted); detk report/util exit 0 doing nothing rather than rejecting (pinned); four accidental behaviours put to Adam as DETK-0033 (Proposed).

## Artifacts

## Findings

## Questions
