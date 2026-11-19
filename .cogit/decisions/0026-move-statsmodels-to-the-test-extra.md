---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/statsmodels-test]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: move statsmodels to test-only dependencies"}
---

# Move statsmodels to the test extra

- Proposed by: the planning session, 2026-11-19, to record Adam's answer

## Background

statsmodels is a runtime dependency of detk (`pyproject.toml`:
`statsmodels>=0.14`; locked at 0.14.6), but the DETK-0024 study found
that no module of `de_toolkit/` imports it. Its only use is the
logistic-regression comparison in `tests/de/test_de.py` (lines
310-336).

## Context

- A runtime dependency that detk does not use still costs every user an
  install, and statsmodels brings patsy (and, from 0.15.0, formulaic)
  with it.
- Only detk and statsmodels depend on patsy in the lock. Once patsy-lite
  runs on formulaic (DETK-0024) and statsmodels is test-only, patsy is no
  longer installed with detk.
- Criteria: what users install; tests keep their statsmodels comparison.

## Options

### Option A: move statsmodels to the `test` extra (and the `dev` group)

Users no longer install statsmodels or patsy. The test that uses it
installs it.

### Option B: keep it as a runtime dependency

No change; users keep installing an unused package.

## Decision

Option A, chosen by Adam on 2026-11-19 (relayed by the driver session):
"move statsmodels to test-only dependencies."

## Consequences

`release/statsmodels-test` moves it, relocks, and adds a check that
detk's modules import without statsmodels. After both this and
`release/formula-migrate`, detk's runtime formula dependency is
formulaic alone: formulaic plus what it pulls in (interface-meta,
narwhals, wrapt, typing-extensions, and numpy, pandas and scipy, which
detk already has). patsy is installed only with the test extra, through
statsmodels.
