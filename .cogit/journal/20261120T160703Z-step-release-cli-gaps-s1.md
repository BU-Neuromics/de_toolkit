---
kind: step
time: 2026-11-20T16:07:03Z
by: DETK/developer
node: release/cli-gaps
step: s1
branch: node/95-cli-gaps
verdict: done
commits: [a86828a, 5e03c2f]
decisions: []
---

# Done: Remove every deprecated `--column-data` (detk-filter, detk-stats summary and pca; DETK-0030); route every failure through one handler giving 0/2/1 with a one-line stderr cause (DETK-0031), help epilogs, cli-pin rows; open the PR

## Summary

s1 done (see the earlier entry): --column-data removed (DETK-0030); one handler cli_main giving 0/2/1 with a one-line stderr cause, traceback under --verbose (DETK-0031); help epilog; cli-pin exit codes pinned; commands.md; CHANGELOG. DETK-0150 accepted (Option A), unblocking the tick. Fix: test_report positional order for Python 3.11's argparse.

## Artifacts

## Findings

## Questions
