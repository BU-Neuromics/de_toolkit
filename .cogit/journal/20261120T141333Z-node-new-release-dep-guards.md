---
kind: action
time: 2026-11-20T14:13:33Z
by: adamlabadorf
action: node-new
node: release/dep-guards
return: 1m11s
---

# New node release/dep-guards

Task release/dep-guards: The runtime-only check fails if patsy (or docopt-ng) comes back as a runtime dependency, and the ruff E402 ignore in pyproject.toml gives its real reason (DETK-0001, DETK-0026)
