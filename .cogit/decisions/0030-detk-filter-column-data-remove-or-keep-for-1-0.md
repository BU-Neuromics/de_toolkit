---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/cli-gaps]
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
