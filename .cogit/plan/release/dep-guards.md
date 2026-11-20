---
kind: task
objective: The runtime-only check fails if patsy (or docopt-ng) comes back as a runtime dependency, and the ruff E402 ignore in pyproject.toml gives its real reason (DETK-0001, DETK-0026)
acceptance:
  - tests/check_runtime_deps.py lists patsy beside statsmodels in TEST_ONLY (patsy still comes into the dev environment through statsmodels), and docopt-ng too now that release/cli-migrate has removed it; its docstring and the success line name what it guards; the 'runtime dependencies only' CI job passes
  - 'shown once by hand, recorded on the PR: with patsy added back to the runtime dependencies (not committed) the check exits non-zero naming patsy'
  - 'the comment on the E402 entry of [tool.ruff.lint] ignore no longer names docopt: it states why module-level code comes before the imports in the detk modules after the argparse migration (the help text and subcommand tables at the top of each command module), or the ignore is dropped if no module needs it any more; ruff passes'
from: [DETK-0001, DETK-0026]
scope: [tests/check_runtime_deps.py, +pyproject.toml]
---

# Guard the removed dependencies and fix the E402 note

## Implementation plan

## Notes
