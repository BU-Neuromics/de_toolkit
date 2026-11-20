---
template: adr
state: Accepted
authority: [DETK/developer]
date: 2026-11-20
supersedes: [DETK-0010]
from: {node: release/cli-migrate, step: s3}
applies: [release/cli-migrate]
allowed_by: [reasonable]
reason: "DETK-0010's mechanism moves from docopt to argparse with the parser it checks against (DETK-0023); the decision itself is unchanged"
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20: a direct consequence of DETK-0001 Option B and DETK-0023 (argparse)"}
---

# Keep the agent skill in step with the CLI through the argparse parsers

## Background

DETK-0010 (Accepted) keeps the `detk` agent skill in step with the CLI
through `tests/skills/test_skills.py`: every `detk-*` command line in a
fenced block must parse, every command, subcommand and option named in the
prose must exist, and the usage blocks copied into
`skills/detk/references/commands.md` must appear in `--help`. Its
mechanism was docopt: the test fed each command line to docopt with the
usage text `--help` printed. release/cli-migrate replaces docopt-ng with
argparse in every command (DETK-0001 Option B, DETK-0023), so that
mechanism no longer exists. The node's acceptance asks for DETK-0010 to be
superseded or revised to say so; cogit revises only Proposed or
Provisional records, so this record supersedes it.

## Context

- With argparse, `--help` is generated and is no longer a grammar a test
  can parse; the parser itself is the source of truth, and each module
  exposes it as `build_parser()`.
- `common.parse_cli(parser, argv)` is the one point every command parses
  from, including the behaviours the cli-pin tests hold (an option given
  twice, `--`, an unknown option named first).
- Help keeps the DETK-0025 Option B layout, which the copied usage blocks
  follow.
- Criteria as in DETK-0010: drift is caught in CI, without a manual step,
  without generating the skill.

## Options

### Option A: check against the argparse parsers

Parse each fenced command line with the command's own parser through
`parse_cli`, exactly as the installed command parses it; take the
subcommands and declared options from the parser; keep matching the
copied usage blocks line for line against `--help`. Everything else in
DETK-0010 stays.

### Option B: check against the `--help` text

Scrape commands, subcommands and options from the help text as before.
Fragile now that help is formatted by argparse (wrapping, the compact
`-o, --output FILE` form), and it would not catch a command line that the
help lists but the parser rejects.

## Decision

Option A. The parser is what the user runs, so checking against it cannot
drift from the CLI; the rest of DETK-0010 (what is checked, in CI, with the
skill written by people) is unchanged.

## Consequences

- `tests/skills/test_skills.py` imports each command's `build_parser()`
  and parses through `common.parse_cli`; a module's parser must be
  importable without R.
- The copied usage blocks change with the new help and are regenerated;
  a change to help wording breaks that check until the block is recopied,
  as before.
- DETK-0010 is superseded by this record; its Option A stays the policy.
