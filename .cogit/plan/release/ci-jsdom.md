---
kind: task
objective: The report's jsdom render tests (tests/report/test_report_view_text.py, the null-rendering test among them) run in CI instead of skipping in every job
acceptance:
  - one CI job (the Python 3.13 test job, or the job the developer judges cheapest) sets up node and installs a pinned jsdom (the version the tests were run with, 25.0.1, or the current release, pinned in the workflow or a package.json and lock under tests/report/) and exports NODE_PATH so _jsdom_available() is true there
  - in that job the jsdom tests fail rather than skip when node or jsdom is missing (an environment variable such as DETK_REQUIRE_JSDOM=1, read by the needs_jsdom marker, as DETK_TUTORIALS_REQUIRE_ALL does for the tutorials); a test of the marker covers both settings; the job's log on the PR shows every needs_jsdom test passed (test_views_with_null_values_render included) and none skipped; other jobs keep skipping them
  - tests/report/test_report_view_text.py's module docstring says which CI job runs the render tests and how to run them locally; ci.yml passes actionlint or the existing workflow checks, and every other job is unchanged
scope: [.github/workflows/ci.yml, +tests/report/test_report_view_text.py, new:tests/report/package.json, new:tests/report/package-lock.json]
issue: 130
visited: 903ac76
status: done
done: 98c213d
---

# CI runs the report's browser render tests

## Implementation plan

- [x] @developer Set up node and a pinned jsdom in one CI job with NODE_PATH, make the jsdom tests required there through an environment variable, test the marker, update the test module's docstring; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: read the job's log and count the needs_jsdom tests that ran and passed, and check the other jobs still skip them <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-21 from the release/strict-json review (#120, not
blocking, note 2): the jsdom tests in tests/report/test_report_view_text.py
skip in every CI job because no job has node and jsdom, so the report's
rendering (including #120's test_views_with_null_values_render) is checked
only when someone runs them locally. The reviewer ran them with jsdom
25.0.1 on NODE_PATH: 12 passed.

The require switch mirrors DETK_TUTORIALS_REQUIRE_ALL (release/tutorial-harness),
so the job cannot pass by skipping. A CI-only change, within DETK-0063, no
decision needed. No node in progress touches ci.yml or this test module, so
it has no prev and is ready now. Before release/cut.
