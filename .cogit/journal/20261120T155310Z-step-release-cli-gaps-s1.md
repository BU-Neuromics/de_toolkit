---
kind: step
time: 2026-11-20T15:53:10Z
by: DETK/developer
node: release/cli-gaps
step: s1
branch: node/95-cli-gaps
verdict: done
commits: [a86828a, 48b5437]
decisions: [DETK-0150]
---

# Done: Remove every deprecated `--column-data` (detk-filter, detk-stats summary and pca; DETK-0030); route every failure through one handler giving 0/2/1 with a one-line stderr cause (DETK-0031), help epilogs, cli-pin rows; open the PR

## Summary

Removed --column-data from detk-filter, detk-stats summary and pca (DETK-0030): options, warnings and handling; cli-pin pins expect exit 2 naming it; tests/report positional; skill usage blocks regenerated from help. One handler common.cli_main on every main (DETK-0031): UsageError/InvalidDesignException exit 2 with usage; other exceptions exit 1 with '<command>: error: <cause>' on stderr, traceback only under --verbose; the sys.exit(1) sites removed; number options that do not convert are usage errors (option_value); R error messages lead with the cause. Help ends with 'exit codes:'. cli-pin: exit 2 for every invalid line, tests/cli/test_cli_exit_codes.py one failure per class (bad file, missing R, missing R package, failing step, R-gated failing R step). commands.md states the codes. CHANGELOG: two Breaking entries. DETK-0150 Proposed: tests/formula bad-design pin (outside scope) now expects exit 2.

## Artifacts

## Findings

## Questions

- DETK-0150 release/cli-gaps pins a bad design's exit 2 in tests/formula, outside its scope (#96)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
