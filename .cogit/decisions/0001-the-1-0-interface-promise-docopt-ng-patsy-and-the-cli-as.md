---
template: adr
state: Proposed
authority: [human]
date: 2026-11-09
from: {node: release}
applies: [release]
issue: 18
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

Recommendation (the proposal on #18): Option A. Closing #18 records it.

## Consequences

The docs statement of #37 stands as written. Revisit docopt-ng if it
becomes a maintenance burden, and patsy if statsmodels drops it.
