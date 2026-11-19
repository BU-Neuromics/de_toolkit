---
template: adr
state: Accepted
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/cli-gaps]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: remove it in 1.0"}
---

# detk-filter --column-data: remove or keep for 1.0

- Proposed by: the planning session, 2026-11-19, under DETK-0025's "address
  all the CLI gaps"

## Background

`detk-filter` has taken the column data file as an optional positional
`[<cov_fn>]` since the 2018 filter overhaul (`18e64ce`). The older
`--column-data=FILE` option is still accepted. It is marked
"DEPRECATED: pass cov_fn as positional command line argument instead"
in help, and warns when used (`filter.py` lines 330-342).

## Context

- No docs, example or skill use `--column-data`.
- 1.0 starts the promise. An option kept in 1.0 has to be kept until
  2.0; one removed now is removed before anyone was promised it.
- Criteria: a clean promised surface; not breaking scripts written for
  0.x.

## Options

### Option A: remove it in 1.0

`detk-filter` accepts only the positional argument. The CHANGELOG lists
the removal as a breaking change from 0.9.

### Option B: keep it, deprecated, through 1.x

It stays in help, marked deprecated, and is removed in 2.0. The promised
surface carries it until then.

## Decision

Option A, chosen by Adam on 2026-11-19 (relayed by the driver session):
"remove it in 1.0". `detk-filter` accepts only the positional column data
argument; the CHANGELOG lists the removal as a breaking change from 0.9.

## Consequences

`release/cli-gaps` carries out the choice. Under A, the pin test for
`--column-data` changes from "accepted with a warning" to "unknown
option".

## Replies

- 2026-11-19, adamlabadorf: Adam, relayed by the driver session 2026-11-19: "yes, sweep the entire project for the deprecated --column-data option and remove them". The removal covers every deprecated --column-data, not only detk-filter's: detk-filter, detk-stats summary and detk-stats pca (de_toolkit/filter.py, de_toolkit/stats.py), their usage blocks in skills/detk/references/commands.md, and tests/report/test_report.py, which passes --column-data to detk-stats summary. detk-util's --column-data-output is a different option and is not deprecated; it stays. No docs page or example uses --column-data. release/cli-gaps carries out the sweep and changes the cli-pin pins of the three deprecation warnings.
