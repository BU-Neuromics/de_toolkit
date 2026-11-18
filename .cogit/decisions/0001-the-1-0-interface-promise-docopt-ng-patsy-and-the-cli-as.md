---
template: adr
state: Accepted
authority: [human]
date: 2026-11-09
from: {node: release}
applies: [release]
issue: 18
revisions:
  - {date: 2026-11-18, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-18: option B, migrate off docopt-ng and patsy before 1.0; the CLI stays the promise; the libraries are DETK-0023 and DETK-0024, open for Adam"}
---

# The 1.0 interface promise: docopt-ng, patsy, and the CLI as the stable surface

- Proposed by: a coding session, from #18 (2026-08-11); recorded here 2026-11-09

## Background

A 1.0 release is a compatibility promise. Two dependencies were kept as
they were through Phase 1 and their question deferred: docopt-ng, which
builds every `detk-*` command line from module docstrings, and patsy,
which `patsy_lite.py` wraps for design formulas. The open question in
#18 is what 1.0 promises and on which libraries.

## Context

- The docstring-as-interface pattern is load-bearing across all 11
  entry points and the docs; the uv and hatchling migration (#30) needed
  no change to it.
- docopt-ng is a community fork of an abandoned project;
  `de_toolkit/test_docopt.py` (0% covered) hints at past friction.
- `patsy_lite.py` is 98% covered; patsy is maintained but feature-frozen,
  formulaic is its successor.
- The docs already state the CLI is the primary interface (#37).
- The full discussion and the proposed text are on #18.

## Options

### Option A: keep both, promise the CLI

docopt-ng and patsy stay for 1.0. Subcommand names, arguments, output
formats, the versioned module JSON schema and the Process Run Crate
provenance follow semver from 1.0; the Python API is not a promise.

### Option B: migrate before 1.0

Move to argparse or click and to formulaic before the tag. Removes two
aging dependencies at the cost of a rewrite on the way to a release.

### Option C: keep both, promise the Python API too

As A, and declare the module-level API public.

## Decision

Option B, chosen by Adam on 2026-11-18 (relayed by the driver session):
replace docopt-ng and patsy before 1.0 is tagged. In his words: "I'm ok
with doing B and switching to better supported libraries before the
release, I'd rather take the pain now than later." He sees detk as
primarily for coding agents, to make agent-written analyses more reliable
and explainable. He considered promising the Python API (Option C, and C
with B) and did not choose it, so the 1.0 promise stays the CLI as in
Option A: subcommand names, arguments, output formats, the versioned
module JSON schema and the Process Run Crate provenance follow semver
from 1.0; the Python API is not a promise.

Which libraries replace them is not decided here: the parser is
DETK-0023 (argparse, click or other) and the formula library DETK-0024
(formulaic or other), both Adam's.

## Consequences

The docs statement of #37 (the CLI is the promise) stands. The migration
is planned under `release`, ahead of `release/cut`: pin each command's
parsing and the formula matrices in tests first (`release/cli-pin`,
`release/formula-pin`), then replace docopt-ng in all 11 entry points
(`release/cli-migrate`, after DETK-0023) and patsy in `patsy_lite.py`
(`release/formula-migrate`, after DETK-0024), then update the docs that
describe the docstring-as-interface pattern and copy usage blocks
(`release/cli-docs`). DETK-0010's skill test, which parses with docopt,
moves to the new parser in `release/cli-migrate`. patsy stays installed
through statsmodels 0.14.
