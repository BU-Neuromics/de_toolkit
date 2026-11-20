---
kind: task
objective: The runtime-only check fails if patsy (or docopt-ng) comes back as a runtime dependency, and the ruff E402 ignore in pyproject.toml gives its real reason (DETK-0001, DETK-0026)
acceptance:
  - tests/check_runtime_deps.py lists patsy beside statsmodels in TEST_ONLY (patsy still comes into the dev environment through statsmodels), and docopt-ng too now that release/cli-migrate has removed it; its docstring and the success line name what it guards; the 'runtime dependencies only' CI job passes
  - 'shown once by hand, recorded on the PR: with patsy added back to the runtime dependencies (not committed) the check exits non-zero naming patsy'
  - 'the comment on the E402 entry of [tool.ruff.lint] ignore no longer names docopt: it states why module-level code comes before the imports in the detk modules after the argparse migration (the help text and subcommand tables at the top of each command module), or the ignore is dropped if no module needs it any more; ruff passes'
from: [DETK-0001, DETK-0026]
scope: [tests/check_runtime_deps.py, +pyproject.toml]
prev: [DETK-0001, DETK-0026, release/cli-migrate]
issue: 90
visited: 9a704f1
status: done
done: 3385157
---

# Guard the removed dependencies and fix the E402 note

## Implementation plan

- [x] @developer Add patsy and docopt-ng to `TEST_ONLY` in `tests/check_runtime_deps.py` (docstring and message to match), show the check failing once with patsy put back by hand, and correct the E402 comment in `pyproject.toml`; open the PR <!-- s1 -->
- [x] @reviewer Review the PR <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 by the planning session on the driver's list of
follow-ups (Adam's delegation, DETK-0063). release/formula-migrate removed
patsy from the runtime dependencies; nothing yet fails if it comes back.
statsmodels depends on patsy, so the check's environment (`uv sync --locked
--no-dev`) is the one place its absence can be checked. After
release/cli-migrate, which removes docopt-ng and edits `pyproject.toml`;
ruff still finds about 100 E402 sites on that branch (the argparse help
text and subcommand tables sit before the imports), so the ignore stays
unless the developer finds otherwise. No CHANGELOG line: nothing a user
sees changes.
