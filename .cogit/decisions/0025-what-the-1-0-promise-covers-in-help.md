---
template: adr
state: Accepted
authority: [human]
date: 2026-11-18
from: {node: release}
applies: [release/cli-pin, release/cli-migrate, release/cli-docs]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's answer relayed by the driver session, 2026-11-19: option B; address all the CLI gaps"}
---

# What the 1.0 promise covers in --help

- Proposed by: the planning session, 2026-11-18, on Adam's answer
  relayed by the driver session. The planning session had assumed help
  text was outside the promise; Adam said otherwise.

## Background

DETK-0001 makes the CLI detk's 1.0 promise: subcommand names, arguments,
output formats, the module JSON schema and the Process Run Crate
provenance. The planning session asked whether the `--help` layout is
part of that promise. Adam answered (2026-11-18, his words): "I think a
fully featured CLI should be promised for 1.0, including help text if
that will enhance the agentic coding flow."

So help text is in the promise, on the condition that promising it
helps agents. This record works out what that means concretely. Adam
decides the scope; the condition is his to apply.

## Context

- detk's main users are coding agents. An agent reads `--help` to find
  which commands exist, what each argument means, what the defaults are,
  and how to write a correct command line. It re-reads help each
  session, so stable facts in predictable places help it. Stable wording
  mostly does not: agents read prose robustly, and frozen wording would
  block making help clearer for them.
- Today: help is the docopt usage block of each command, printed
  verbatim. Most subcommands have a description, usage lines and an
  options list with defaults. Few have a runnable example: `stats` and
  `util` mention examples in prose. The agent skill's
  `references/commands.md` and `docs/tools/*.md` hold hand-copied usage
  blocks. DETK-0010's test checks the skill's copies against `--help`.
- argparse (DETK-0023) generates help from the parser. Section order,
  option lists, defaults and choices therefore come from code and can be
  checked by tests. The parser can also be walked to emit the same
  information as data.
- Criteria: what an agent can rely on; what a test can check; freedom
  to improve wording after 1.0; cost before the tag.

## Options

### Option A: promise the structure and the facts, not the wording

From 1.0, every command and subcommand answers `-h`/`--help` on stdout
with exit 0. Help has a fixed section order: description, usage,
positional arguments, options, common options. It lists every
positional and option with its name, metavar, default and choices, and
a one-line description. Removing or renaming any listed item, or
changing a default, is a breaking change under semver, as it already is
for the arguments themselves. Wording and layout within a section may
improve in any release. Tests check the structure and facts.

### Option B: A, plus tested examples in help

As A, plus each subcommand's help ends with at least one example command
line. CI checks that each example parses and, where test data allows,
runs. Examples are the part of help agents copy most directly. Testing
them stops them going stale the way the docs examples did (#43).

### Option C: A or B, plus machine-readable help

As A or B, plus `detk-x --help-json` (or `detk help --json`) prints the
commands, arguments, types, defaults, choices and examples as JSON in a
versioned schema, promised like the module JSON schema. An agent or tool
gets the CLI's shape without parsing text, and the skill's references
and the docs could be checked against it (or generated from it). One
more promised schema to maintain. It adds a new option to every command,
which is new scope before the tag.

### Option D: freeze the help text

Golden-file tests of the exact `--help` output; any wording change is a
breaking change. Fully predictable, but it stops help from improving for
agents after 1.0. The condition in Adam's answer argues against it.

## Decision

Option B, chosen by Adam on 2026-11-19 (relayed by the driver session):
"DETK-0025 - B. address all the CLI gaps." From 1.0, help promises its
structure and facts: section order; every positional and option with
its metavar, default, choices and a one-line description; and at least
one example command line per subcommand, which CI checks. Wording may
improve in any release. All seven gaps listed below are in scope for
1.0. Those that need a choice Adam has not made are DETK-0029
(`--size-factors`), DETK-0030 (`--column-data`), DETK-0031 (exit codes)
and DETK-0032 (shell completion).

## Consequences

Under A or B: `release/cli-pin` pins help facts (names, metavars,
defaults, choices, exit 0 on stdout), not wording. `release/cli-migrate`
delivers help in the agreed section structure on argparse.
`release/cli-docs` documents the help promise beside the #37 statement.
Under B, `release/cli-migrate` also adds examples and their test. Under
C, a further node adds the JSON help and its schema. Under D,
`release/cli-pin` adds golden help files after the migration, since the
text changes with argparse anyway.

### "Fully featured CLI": gaps noticed today (candidates, not scope)

Seen while reading the code on 2026-11-18. Each is a candidate for Adam
to promote into 1.0 or leave out:

1. The umbrella `detk` command lists `report` and `util` in its usage
   but rejects them: `main` in `common.py` checks `argv[1]` against a
   `cmds` tuple that lacks `enrich`, `report` and `util`, so
   `detk enrich|report|util ...` prints the usage instead of running.
   Its `elif cmd == "enrich"` branch is unreachable, and its usage omits
   `enrich`.
2. `detk-norm deseq2` declares `--size-factors=FILE` but never reads it
   (`norm.py` line 26 is its only mention). Help promises an option
   that does nothing (already an open question in the stop notes).
3. Option metavars are mostly consistent (`--output=FILE` 28 times),
   with a few exceptions: `-o <out_fn> --output=<out_fn>` in
   `detk-filter`, `--rda=RDA` beside `--rda=FILE`, and
   `--routput-dir=DIR` beside `--routput-dir=PATH`.
4. `detk-filter` still offers `--column-data`, marked DEPRECATED in its
   help. 1.0 is the point to drop it or to promise it.
5. Exit codes are not documented in help or the docs, so an agent cannot
   tell from them a usage error from a bad input file or a failed R
   step.
6. `--version` is handled before parsing in each `main`, and help shows
   the version as a header line. That is fine, but the behaviour is
   implicit, not declared.
7. No shell completion. argparse needs a further package (argcomplete)
   for it. Probably low value for agents.
