---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/cli-gaps]
---

# Exit codes of the detk commands

- Proposed by: the planning session, 2026-11-19, under DETK-0025's "address
  all the CLI gaps"

## Background

An agent running detk decides what to do next from the exit code and
stderr. Today exit codes are not documented. In practice: a usage error
exits through docopt with status 1 and the usage block; handled errors
call `sys.exit(1)` (25 places across the modules); an unhandled
exception exits 1 with a traceback. Success is 0. Everything that fails
is therefore 1.

## Context

- argparse (DETK-0023) exits **2** on a usage error by default. The
  migration changes that code unless detk overrides it.
- Under the 1.0 promise, documented exit codes become part of the CLI.
- Useful distinctions for an agent: a wrong command line (fix the
  command), bad input data (fix the files), a missing dependency such as
  R or an R package (fix the environment), and a failure inside a step
  (look at the log).
- Criteria: an agent can act on the code; follows convention; few
  enough to keep.

## Options

### Option A: 0 / 1 / 2 (recommended)

0 success; 2 usage error (argparse's default and the common Unix
convention); 1 any other error, with a one-line message on stderr naming
the cause and no traceback unless `--verbose`. Documented in help and
the docs.

### Option B: A, plus distinct codes for environment and input

As A, plus 3 for a missing dependency (R or an R package) and 4 for
invalid input data. More for an agent to act on, but more to keep
consistent across 25 exit points.

### Option C: keep 1 for every failure

Override argparse back to 1. Nothing changes; agents read stderr.

## Decision

Open for Adam. The planning session recommends Option A: the usage/other
split is the distinction agents act on most, and it is what argparse
gives anyway.

## Consequences

`release/cli-pin` pins exit codes as non-zero for now. `release/cli-gaps`
sets the codes, makes stderr messages consistent, and updates the pins.
`release/cli-docs` documents them.
