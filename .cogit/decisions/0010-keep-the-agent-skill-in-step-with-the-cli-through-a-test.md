---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/agent-skills, step: s1}
applies: [release/agent-skills]
allowed_by: [reasonable]
reason: skill command lines and copied usage blocks are checked against the installed CLI in CI, so drift fails a build rather than misleading an agent
---

# Keep the agent skill in step with the CLI through a test against --help

## Background

The `detk` agent skill (DETK-0009) tells an agent which commands and options
to run. The CLI is detk's 1.0 promise (DETK-0001), but it still grows (#24,
#29, #25), and a skill that names an option the installed CLI lacks sends an
agent into errors it will try to work around. Something has to keep the
skill and the CLI in step.

## Context

- Every `detk-*` command builds its command line from a docopt usage block,
  and `<command> <subcommand> --help` prints it, so the installed CLI can
  say what is valid.
- The skill holds command lines in `bash` blocks and, in
  `references/commands.md`, usage blocks copied from `--help`.
- CI already runs pytest on every pull request, without R; `--help` needs no
  R.
- Criteria: drift is caught before a release, without a manual step, and
  without generating the skill (the prose around commands is the value).

## Options

### Option A: a test against `--help`

`tests/skills/test_skills.py` checks each skill's front matter, that every
`detk-*` line in a `bash` block names a real command and subcommand and only
options its usage lists, and that every line of a usage block under a
``## `detk-x sub` `` heading appears in that command's `--help`. Cheap,
runs in the existing CI, fails with the line to fix.

### Option B: generate `references/commands.md` from the docstrings

Always current for usage, but the `SKILL.md` command lines would still go
unchecked, and a generator is one more tool to maintain.

### Option C: review only

Rely on the reviewer of each CLI change to update the skill. Nothing checks
it, and it is the step most easily forgotten.

## Decision

Option A. It checks both the prose command lines and the copied usage, in
the CI that already runs, and leaves the writing of the skill to people.

## Consequences

- A pull request that renames or removes an option or subcommand used by the
  skill fails `tests/skills` until the skill is updated; adding a new option
  does not, so new commands still need adding to the skill by hand (the
  notes of #38 list #24, #29 and #25).
- The test does not check what a command does, only that it parses; the
  reviewer step of #38 runs the skill on the airway example for that.
- Revisit if the skills come to hold commands in another form than `bash`
  blocks, or if a usage block is ever intentionally abridged.
