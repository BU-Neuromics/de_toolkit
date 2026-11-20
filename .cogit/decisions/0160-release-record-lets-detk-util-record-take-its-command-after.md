---
template: adr
state: Proposed
authority: [human]
date: 2026-11-20
from: {node: release/record, step: s1}
applies: [release/record]
issue: 104
---

# release/record lets detk-util record take its command after --, in common.parse_cli outside its scope

- Proposed by: the release/record developer session, 2026-11-20 (step s1)

## Background

DETK-0061 (Accepted) gives `detk-util record` the command line
`detk-util record [options] -i FILE... -o FILE... -- <command> [<arg>...]`:
everything after `--` is the external command, run as given. Every detk
command parses through one function, `common.parse_cli`, and since
release/cli-migrate it refuses `--` outright ("unrecognized arguments:
--"), because docopt took `--` for an undeclared argument rather than an
end-of-options marker; `tests/cli/test_cli_behaviours.py::
test_double_dash_is_not_an_end_of_options_marker` pins that for every
command. `parse_cli` also scans every word for an unknown option before
parsing, so a command such as `mlr --icsv ...` would be refused as detk's
unknown option `--icsv`. `de_toolkit/common.py` is not in release/record's
scope.

A second, smaller file outside the scope: `docs/report.md` documents the
module JSON envelope with a field table and "schema_version, currently
**1.0**". The node raises the schema to 1.1 and adds the optional
`in_file_paths` and `out_file_paths`, so that page goes stale.

## Context

- The acceptance cannot be met without `parse_cli` taking `--` for this
  one subcommand: there is no other route from the command line to the
  parser, and the cli-pin adapter (`tests/cli/cli_adapter.py`) stops
  every command at `parse_cli`, so splitting the command line before it
  in util.py would leave the command out of everything the cli-pin
  tables can check.
- Every other command must keep refusing `--` (the existing pin).
- Criteria: the smallest change to the shared parser; no change to any
  other command's behaviour; the record's command reaches the cli-pin
  tables like any other argument; parallel nodes (release/help-options
  is in progress on tests/cli/) see a small, local diff.

## Options

### Option A: a parser opts in with `command_dest`; parse_cli splits at the first `--` (recommended)

`parse_cli` reads `command_dest` from the subcommand's parser (only
record's sets it, to `"command"`). For such a parser, the words after the
first `--` are the command, set on the namespace as a list; only the words
before it are scanned for unknown options and parsed. A word before `--`
that would land in the command is a usage error ("the command to run goes
after --"). For every other parser `--` is refused exactly as now. The
diff is about twenty lines in one function; the record subparser keeps a
`<command>` positional (nargs `*`) only so help and the completion
scripts list it.

`docs/report.md`'s envelope section is updated in s3 (with
`docs/tools/util.md`) to say 1.1 and list the two optional fields.

### Option B: split the command line in util.main before parse_cli

No change to common.py, but `parse_cli` then never sees the command, so
the cli-pin tables (parse, invalid lines) cannot pin it, and `detk util
record` through the umbrella and the help test's example parsing would
need their own route around the shared parser. More code, less checked.

### Option C: a separate node changes parse_cli first

Blocks release/record on a twenty-line change that only it needs.

## Decision

Recommended: Option A, with the docs/report.md update in s3. It is the
direct consequence of DETK-0061's command line, it changes nothing for
any other command (the existing `--` pin still passes, and the record's
own pins check the split), and it is local to one function. Awaiting the
driver's / Adam's answer; the node's PR branch carries Option A.

## Consequences

`de_toolkit/common.py` (the `--` handling in `parse_cli`) and
`docs/report.md` (the envelope section) join release/record's scope. The
cli-pin tables gain three generic fields so they can state record's
command line: `Opt.repeat` (a repeatable option yields a list),
`Opt.required`, and `Pos.after_dashdash` (the words after `--`), with the
case generator (`tests/cli/cli_cases.py`) putting generated arguments
before a `--`. A later subcommand that runs another command would set
`command_dest` the same way.
