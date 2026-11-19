---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/statsmodels-test]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19, to the stop note's open question on environment.yml: delete it"}
---

# Delete environment.yml

- Proposed by: the planning session, 2026-11-19, to record Adam's answer
  to the open question in the stop note of 2026-11-19 20:12 UTC

## Background

`environment.yml` is a conda environment file at the repository root. It
lists docopt, future, sphinx, sphinx-autobuild, patsy and
`statsmodels>=0.8.0`, among others, all through pip, with no Python
version.

## Context

- Nothing refers to it: not the README, the docs, CI or `pyproject.toml`.
  detk is installed with pip or uv from `pyproject.toml` and `uv.lock`.
- It is out of date in ways that would mislead: docopt and patsy are
  being removed (DETK-0001), statsmodels is becoming test-only
  (DETK-0026), and the docs moved from sphinx to MkDocs (DETK-0004).
- Three nodes had it in scope only to keep it in step:
  `release/cli-migrate`, `release/formula-migrate`,
  `release/statsmodels-test`.

## Options

### Option A: delete it

One source of dependencies, `pyproject.toml`. Nothing to keep in step.

### Option B: bring it up to date

A conda route for users who want one; a second list to keep in step with
`pyproject.toml`.

## Decision

Option A, chosen by Adam on 2026-11-19 (relayed by the driver session):
"delete it".

## Consequences

`release/statsmodels-test` deletes it, since it already edits the
dependency files first among the three. `release/cli-migrate` and
`release/formula-migrate` no longer list it. The CHANGELOG notes the
removal.
