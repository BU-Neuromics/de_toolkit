---
kind: step
time: 2026-11-22T18:14:02Z
by: DETK/developer
node: release/jsdom-summary
step: s1
branch: node/146-jsdom-summary
verdict: done
commits: [29c64f0]
decisions: []
---

# Done: Make the render-test step check only pytest's final summary line, show the check on the four sample outputs in the PR, put the functools import in order; open the PR

## Summary

The 'Report render tests ran in jsdom' step now reads only pytest's final line: tail -n 1 of the tee'd -v -rs output piped to one awk command that prints 'pytest summary: <line>' and exits 0 only if the line matches '[0-9]+ passed' and no '[0-9]+ (failed|errors?|skipped|xfailed|xpassed)'. Shown on four samples (all passed with test_error_message_failed in the listing: 0; '1 failed, 11 passed': 1; '11 passed, 1 skipped': 1; '11 passed, 1 error': 1). functools import sorted (ruff --select I passes). Within the node: warnings and deselected counts are allowed (acceptance lists only failed/error/skipped/xfailed/xpassed); pytest's own non-zero exit still fails the step first through pipefail. Locally: ruff check/format pass, the test module passes (jsdom tests skip without NODE_PATH); the workflow parses as YAML. actionlint and a local jsdom run were not run here (the session's permissions blocked the downloads); CI's 3.13 job runs the step. No other job or step changed.

## Artifacts

## Findings

## Questions
