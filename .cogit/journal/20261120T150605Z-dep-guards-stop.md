---
kind: stop
time: 2026-11-20T15:06:05Z
by: DETK/developer
node: release/dep-guards
branch: node/90-dep-guards
---

# dep-guards: s1 done, PR #91 for @reviewer

## Done

6f5211c: TEST_ONLY in tests/check_runtime_deps.py guards statsmodels, patsy and docopt-ng (import name -> package; message, docstring and success line name them); shown failing (exit 1, "patsy is installed") with patsy put back by hand, recorded on PR #91; E402 comment now names the help text and SUBCOMMANDS tables before imports (ignore kept: 101 sites). CI green on all 12 checks.

## Stopped because

s2 is @reviewer's

## Next

@reviewer s2 on PR #91

## Open questions

None
