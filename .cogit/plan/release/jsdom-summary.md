---
kind: task
objective: The 'Report render tests ran in jsdom' CI step decides pass or fail from pytest's final summary line alone, so a passing test whose name holds 'error' or 'failed' cannot fail CI, and test_report_view_text.py's imports are in order
acceptance:
  - 'the step in .github/workflows/ci.yml takes the last line of the pytest output (the ''=== N passed in Xs ==='' summary) and fails unless it reports passed tests and no failed, error, skipped, xfailed or xpassed count; the check is one command whose behaviour the PR shows on four sample outputs: all passed with a test named test_error_message_failed in the -v listing (passes), ''1 failed, 11 passed'' (fails), ''11 passed, 1 skipped'' (fails), ''11 passed, 1 error'' (fails); the job''s log on the PR shows the step passing with the summary line printed'
  - tests/report/test_report_view_text.py imports functools in alphabetical order with the other standard-library imports (ruff check --select I on the file passes, or the order ruff's isort rule gives); the needs_jsdom tests still pass in the 3.13 job and skip in the others; actionlint (or the existing workflow checks) passes and every other job and step is unchanged
scope: [.github/workflows/ci.yml, +tests/report/test_report_view_text.py]
issue: 146
visited: 501927d
---

# The render-test CI step reads only pytest's summary line

## Implementation plan

- [x] @developer Make the render-test step check only pytest's final summary line, show the check on the four sample outputs in the PR, put the functools import in order; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: run the check on the sample outputs, read the 3.13 job's log for the summary line and the count of needs_jsdom tests <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-22 from the release/ci-jsdom review (#132, not
blocking). The step 'Report render tests ran in jsdom' in ci.yml runs
`grep -Eq "skipped|SKIPPED|failed|error"` over the whole `pytest -v -rs`
output, so a passing test whose name or parameter id holds `error` or
`failed` (the -v listing prints every name) fails CI. Only the final
summary line says whether tests failed, errored or skipped. Also
`import functools` sits between `shutil` and `subprocess` in
tests/report/test_report_view_text.py.

CI-only, within DETK-0063, no decision. No unfinished node touches
ci.yml or that test module, so it is ready now. Before release/cut.
