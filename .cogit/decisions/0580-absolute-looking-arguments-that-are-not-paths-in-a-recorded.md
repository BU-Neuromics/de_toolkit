---
template: adr
state: Accepted
authority: [human]
date: 2026-11-23
from: {node: release/cli-docs, step: s2}
applies: [release/cli-docs]
revisions:
  - {date: 2026-11-23, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A, under Adam's delegation via the driver session, 2026-11-20 (DETK-0063): within the 1.0 scope and does not change the 1.0 promise. Implemented in release/cli-docs (not a separate node), so the docs and the code land together."}
---

# Absolute-looking arguments that are not paths in a recorded command line

## Background

Every command line detk records (a detk command's `argv`, and the step
`detk-util record -- PROGRAM ARGS...` runs) is written with each absolute
path made relative to `workdir` (DETK-0281), so the report directory can be
moved. `relative_arg` in `de_toolkit/report.py` decides what is a path by
`os.path.isabs(arg)` alone: any argument that starts with `/` is rewritten
with `os.path.relpath`, which also normalizes it. An argument that starts
with `/` but is not a path is therefore rewritten too. Found in review of
PR #163 (release/cli-docs); the developer reported the first case:

| typed (run in `/home/me/proj`) | recorded |
|---|---|
| `sh -c "/usr/bin/env echo hi"` | `sh -c "../../../usr/bin/env echo hi"` |
| `awk '/^gene/ {print}' in.csv` | `awk '../../../^gene/ {print}' in.csv` |
| `grep -E '/^g1,/'` (any `/regex/`) | `'../../../^g1,'` (trailing `/` lost) |

The first still re-runs from `workdir` (the relative path names the same
file). The awk and regex cases do not: the recorded line is a different
program, so the provenance misstates what ran, silently.

## Context

- The recorded `argv` and the crate are part of the 1.0 promise
  (DETK-0001, DETK-0063); a recorded line should re-run as typed from
  `workdir` (DETK-0281, DETK-0390).
- `detk-util record` exists to record arbitrary tools (awk, sed, grep,
  Miller, sh -c), whose arguments often start with `/` without being
  paths. detk's own commands rarely take such arguments.
- release/cli-docs is the last node before release/cut; its docs/report.md
  says a quoted argument is "written as typed", which is not true for one
  that starts with `/`.
- The fix is small and local to `relative_arg` (and `program_arg`, which
  falls back to it), with tests in tests/report/.

## Options

**A. Follow-up fix node before release/cut (block the cut, not
release/cli-docs).** Rewrite an absolute argument only when it looks like
a path: no whitespace, and its parent directory exists (or it exists);
otherwise keep it as typed. `/usr/bin/env echo hi`, `/^gene/ {print}` and
`/^g1,/` are then kept; `/home/me/proj/out.csv` (not yet written, its
directory there) is still rewritten. release/cli-docs's report.md is
updated by that node. Cost: one small node; 1.0 ships with correct
records.

**B. Ship 1.0 as is, fix in 1.0.1.** docs/report.md states the limit now
(an argument starting with `/` is rewritten as a path, so do not start a
script or pattern with `/`). Cost: 1.0's records of such steps are wrong,
and 1.0.1 changes what is recorded for them (a bug fix under semver).

**C. Never rewrite inside `detk-util record`'s command, only in detk's own
argv and `-i`/`-o`.** Simplest and never corrupts a tool's argument, but
gives up DETK-0281's relocation for absolute paths typed as a recorded
tool's arguments (`cp /abs/a /abs/b` without `sh -c`), which the page
documents as rewritten.

## Decision

Recommended: **A**. The awk and regex cases record a command that did not
run, which is the one thing provenance must not do, and it is a small,
contained fix that fits before the cut. release/cli-docs need not wait on
it: its docs are right for every case it shows, and its report.md bullet
on quoted arguments gains a sentence on the `/` case (either "is kept"
after A, or the limit as B states it), done in whichever node lands
second.

## Consequences

- A new task node (e.g. release/record-args) after release/cli-docs and
  before release/cut: `relative_arg` keeps an absolute-looking argument
  with whitespace or a missing parent directory as typed; tests with the
  three rows above and a not-yet-written absolute output; docs/report.md
  and the CHANGELOG say so.
- The heuristic can still misread a bare `/regex/`-like argument whose
  parent happens to exist (`/tmp/`); revisit if a reported case shows it.
