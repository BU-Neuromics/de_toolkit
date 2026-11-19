---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/cli-gaps]
---

# Shell completion for the detk commands

- Proposed by: the planning session, 2026-11-19, under DETK-0025's "address
  all the CLI gaps"

## Background

detk has no shell completion. Adam asked for it in 1.0 with the other
CLI gaps. argparse has no completion of its own; it needs a library.

## Context

- Completion mostly helps people at a terminal. Agents read `--help`
  instead (DETK-0025).
- Criteria: runtime dependencies added (DETK-0026's direction is
  fewer); installation effort for users; upkeep as commands change.

## Options

### Option A: argcomplete

Completes at run time from the argparse parsers. Users run
`register-python-argcomplete` (or activate it globally) once. A small
runtime dependency, plus a marker comment in each entry point.

### Option B: shtab, generating static scripts

shtab generates bash, zsh and tcsh completion scripts from the parsers.
detk would ship them as files (or print them with `detk completion
bash`). Generating needs shtab; using the scripts needs nothing. If they
are generated at build time, shtab is a dev or build dependency only,
not a runtime one. A test keeps the scripts current.

### Option C: a `detk completion <shell>` command with shtab at runtime

As B, but generated on demand. One runtime dependency, nothing to keep
in sync.

## Decision

Open for Adam. The planning session recommends Option B: completion
with no runtime dependency, in keeping with DETK-0026.

## Consequences

`release/cli-gaps` adds the completion, a test that it covers every
command, and a docs section on enabling it.
