---
template: adr
state: Proposed
authority: [human]
date: 2026-11-18
from: {node: release}
applies: [release/cli-migrate, release/cli-docs]
---

# The command-line parser that replaces docopt-ng

- Proposed by: the planning session for DETK-0001 Option B, 2026-11-18

## Background

Adam chose Option B of DETK-0001 (#18): replace docopt-ng and patsy
before 1.0 is tagged. Today every `detk-*` command (11 entry points, about
30 subcommands) builds its command line from a docopt usage block in the
module docstring or `cmd_opts`; `common.py` appends the shared options
(`_cli_doc`), and `--help` prints the block as written. Which library
replaces docopt-ng was named only as "argparse or click" in DETK-0001, and
Adam has not chosen one. The migration nodes under `release` wait on this
record.

## Context

- The 1.0 promise stays the CLI (DETK-0001): subcommand names,
  arguments, output formats, the module JSON schema and the Process Run
  Crate provenance. The migration must accept the same command lines and
  write the same outputs; `release/cli-pin` pins that in tests before
  the parser changes.
- detk's main users are coding agents (Adam, 2026-11-18): what matters is
  a command line that errors clearly on a wrong argument, `--help` that
  says what is valid, and a parser agents already know well.
- docopt matches a unique prefix of a long option (`--out` for
  `--output`). Whether anyone relies on that is unknown; a parser that
  does not do it would reject such command lines.
- DETK-0010 (Accepted) checks the agent skill by parsing its command lines
  with each command's docopt usage; that test moves to the new parser,
  and the usage blocks copied into `skills/detk/references/commands.md`
  and `docs/tools/*.md` change with the new `--help` text.
- Criteria: compatibility of accepted command lines; dependencies added;
  clarity of errors and `--help` for agents; effort across 11 modules;
  maintenance after 1.0.

## Options

### Option A: argparse

The standard library: no dependency. Subcommands through subparsers;
long-option prefix matching on by default (`allow_abbrev`), as docopt
does. `--help` is generated, so its layout changes. Verbose to write by
hand; a small helper in `common.py` would carry the shared options.

### Option B: click

A maintained third-party library (Pallets), already common in scientific
Python. Commands and groups as decorated functions, `CliRunner` for
tests, good error messages. One new dependency. Does not match option
prefixes, so `--out` for `--output` would stop working. `--help` layout
changes.

### Option C: something else (for example typer, on top of click)

Type-hint driven command definitions; two new dependencies and more
indirection. Listed so the choice is not only between A and B.

## Decision

Option A, argparse, chosen by Adam on 2026-11-18 (relayed by the driver
session): "Let's use argparse and formulaic, though I'd like to see how
much work the migration from patsy to formulaic will be before formally
deciding." The formulaic half is DETK-0024 and stays open.

## Consequences

`release/cli-migrate` carries out the choice; under every option
DETK-0010's test is rewritten on the chosen parser and the copied usage
blocks regenerated. Under B or C, command lines that rely on long-option
prefixes break, and the CHANGELOG says so.
