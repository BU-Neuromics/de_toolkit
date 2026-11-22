---
template: adr
state: Proposed
authority: [human]
date: 2026-11-22
applies: [release/record-program, release/cli-docs]
---

# Paths outside the working directory's tree in the report: docs only, or record's program by name

## Background

Since release/report-paths (DETK-0280, DETK-0281), no path in module JSON
or the crate is absolute: `workdir` is relative to the report directory,
and every file path, and every absolute path typed in `argv` or in
`detk-util record`'s params, is relative to `workdir`. A relative path
still spells the directories it climbs through. In review of PR #134 the
reviewer found two cases where that leaves little better than the absolute
path:

- the report directory in another tree from the working directory
  (`--report-dir /tmp/rep` run in `/home/<user>/proj`) gives
  `workdir: ../../home/<user>/proj`;
- an absolute program given to `detk-util record` (`detk-util record --
  /usr/bin/cp a b`) is written `../../../../../../usr/bin/cp`, its depth
  set by how deep the working directory is, so it also hints at the
  machine's layout and stops re-running if the project moves.

docs/report.md already says the `../` chain names those directories and to
keep the report directory and data under the working directory.

## Context

Adam's instruction (2026-11-20, carried out by DETK-0280 and DETK-0281):
published reports and crates hold no absolute machine path. The
reviewer's question is whether 1.0 needs more than the note.

Criteria: (1) no absolute machine path, and no more of the machine's
layout than the user's own choice of layout puts there; (2) report
directory + `workdir` + path still locates every file, the rule
docs/report.md documents and schema 1.2 promises; (3) a recorded command
line re-runs the same; (4) small enough to land before release/cut,
within DETK-0063.

## Options

**A. Docs only.** Keep both as they are; release/cli-docs extends the note
in docs/report.md with the record example. (1) partly: `/usr/bin/cp`
becomes a `../` chain whose depth is the working directory's; (2) yes;
(3) only from the same working directory depth; (4) yes.

**B. Record's program by name when PATH finds it; `workdir` docs only.**
In `detk-util record`, the program (the first word after `--`) typed as an
absolute path is written as its bare name when `shutil.which(name)` finds
that same file (`/usr/bin/cp` becomes `cp`), as `argv[0]` of a detk
command is already its name (DETK-0280); otherwise it is relative as
today. `workdir` stays as it is: any form of a directory outside the
report directory's tree names it, and dropping it would break criterion
(2); release/cli-docs documents both. (1) yes for system programs; (2)
yes; (3) yes wherever PATH finds the same program, which is what the user
relied on; (4) yes, a few lines in `run_record` and its tests.

**C. B, and `workdir` blanked or replaced by a marker when it climbs out to
the filesystem root.** (1) yes; (2) no: the reader can no longer locate
the files, and schema 1.2 would need a new meaning for `workdir`, a change
of the 1.0 promise. Rejected.

## Decision

Recommended (planning session, 2026-11-22; not accepted): **B**. The
`../../usr/bin/cp` form is the one case where the relative rule makes the
record worse than what the user typed and depends on where the project
sits; writing the program by name, when PATH resolves it to the same
file, matches how detk already records its own `argv[0]` and re-runs the
same. The `workdir` chain follows from the user's choice of report
directory, cannot be removed without breaking the location rule, and is
best handled by the existing advice, documented in release/cli-docs.

## Consequences

Under B: release/record-program changes `run_record`'s program entry, with
tests and a CHANGELOG line; release/cli-docs documents the rule and the
`workdir` chain. Under A: release/record-program is closed as not
planned and release/cli-docs alone carries the note. Revisit if a user
needs an absolute program recorded exactly, which B still does for a
program PATH does not find.
