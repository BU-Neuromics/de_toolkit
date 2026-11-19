---
kind: step
time: 2026-11-19T20:47:09Z
by: DETK/reviewer
node: release/cli-pin
step: s2
branch: review/cli-pin
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: every entry point and subcommand covered, expectations independent of docopt, help facts pinned and wording left free (DETK-0025 Option B)

## Summary

Approved on second review: help defaults now tied to their statement (0 of 114 vacuous), stats --column-data warnings pinned; checks pass

## Artifacts

## Findings

Second review, on b7c6660. Checks: `pytest tests/cli`: 1,300 passed, 1 skipped. Full suite: 1,666 passed, 63 skipped (R-gated, run in CI). `ruff check` and `ruff format --check` are clean.

Blocking item fixed: `stated_default` now requires the value to follow the word "default", and the value can't be the start of a longer number or word. I repeated my check: with `[default: ...]` removed from each entry, none of the 114 default assertions passes, where 12 used to. With help reworded argparse-style, as `(default: X)`, all of them still pass, so the wording stays free per DETK-0025 B. Prefix cases are handled: "1" doesn't match "[default: 10]" and "0" doesn't match "[default: 0.25]".

The other changes are sound:
- The `--column-data` deprecation-warning pin now covers detk-stats summary and pca as well as detk-filter.
- The stale `--json`/`--html` text in the detk-stats docstring is noted on release/cli-migrate.
- DETK-0033 is recorded as Accepted (Option A), and release/cli-migrate's acceptance, `from:` and notes follow from it. The skipped rlog test names that outcome.

Note for Adam: the DETK-0033 acceptance (1a683f6) is recorded as your answer, relayed by the driver session. Please confirm it's yours.

## Questions
