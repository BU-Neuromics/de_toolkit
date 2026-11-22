---
template: adr
state: Accepted
authority: [human]
date: 2026-11-22
from: {node: release/report-paths, step: s2}
applies: [release/report-paths]
issue: 137
revisions:
  - {date: 2026-11-22, by: adamlabadorf, change: Accepted, why: "from the terminal: Option B, from the terminal: Adam's delegation via the driver session, 2026-11-20 (DETK-0063): every typed absolute path is written relative to workdir in argv and in detk-util record's params and properties; carries out Adam's instruction that published reports and crates hold no absolute machine paths"}
---

# Absolute paths typed into argv and params in module JSON and the crate

## Background

DETK-0280 (Accepted, Option A) moved the Process Run Crate into the report
directory and made the recorded paths relative, because Adam asked that
no absolute machine path appear in a published report or crate. Its
acceptance names five module JSON fields: `workdir`, `argv[0]`,
`in_file_path`, `out_file_path`, `column_data_path` (and the 1.1 lists).
The command line holds paths in other places too, and so does
`detk-util record`'s document. In review of PR #134 these still carry a
path exactly as typed, so an absolute path typed on the command line
reaches the module JSON, the report's embedded payload and the crate.

## Context

Seen in review (PR #134 at 3e13a88), in one working directory:

- `detk-stats summary --report-dir b -o summ.csv $PWD/counts.csv`: every
  module JSON's `argv` holds the absolute path of counts.csv (and of the
  report directory when `--report-dir` is typed absolute), while
  `in_file_path` is `counts.csv`.
- `detk-util record -i $PWD/samples.csv -o $PWD/copy.csv --tool cp
  --tool-version 1 -- cp $PWD/samples.csv $PWD/copy.csv`: `argv`,
  `params.argv`, `params.command`, `params.inputs`, `params.outputs` and
  `properties.inputs[].path` / `properties.outputs[].path` hold the
  absolute paths; the crate's `PropertyValue`s for the parameters carry
  them too (four occurrences), though its File `@id`s are `../samples.csv`
  and `../copy.csv`.

With paths typed relative, nothing absolute is written: the node's
objective ("for a run given relative paths") is met. But docs/report.md
says "No recorded path names a directory of the machine the analysis ran
on" and the CHANGELOG says "Module JSON (schema 1.2) holds no absolute
path of the machine", which is untrue whenever a path is typed absolute,
and the acceptance says "an absolute path typed on the command line is
written relative too".

Criteria: Adam's ask (no absolute machine path in a published report or
crate); a recorded command line still says what was run and re-runs
from `workdir`; a simple rule a reader can rely on; small change before
1.0.

## Options

**A. Keep argv and params as typed; narrow the docs.** The five fields
stay relative; docs/report.md, the schema and the CHANGELOG say `argv`
and `params` hold the arguments as typed, so an absolute path typed
there is recorded absolute. No code change. Fails Adam's ask for anyone
who types absolute paths (scripts and workflow managers commonly do),
and record's crate leaks them into a published crate.

**B. Write every typed absolute path relative to `workdir`, everywhere.**
In `argv[1:]` a token that is an absolute path, or `--opt=/abs/path`, is
written relative to `workdir` (`os.path.relpath`, POSIX form, as the file
fields already are); `record`'s `params.argv`, `params.inputs`,
`params.outputs`, `properties.*[].path` the same, and `params.command`
rebuilt with `shlex.join` from the rewritten argv. The command line still
re-runs identically from `workdir`. Meets Adam's ask and makes the docs'
sentence true. Cost: `argv` is no longer byte-for-byte as typed (the
schema description says so), and the rule is a token heuristic (a filter
expression or formula never starts with `/`, so false positives are
unlikely; a path not under `workdir` becomes a `../` chain).

**C. Relativize record's file fields only.** `properties.*[].path`,
`params.inputs` and `params.outputs` relative; `argv` and
`params.argv`/`command` as typed, documented as A. Fixes the clearly
path-typed fields, leaves the command line leaking.

## Decision

Recommended (reviewer, not accepted): **B**. It is the only option under
which the published report and crate hold no absolute machine path
whatever the user typed, which is what Adam asked for and what the docs
already claim; and a command line relative to `workdir` re-runs the same
from where it ran. A is acceptable only if Adam is content with the
promise holding for relative paths alone, in which case the docs and
CHANGELOG sentences must be narrowed.

## Consequences

Under B: a helper in report.py rewriting argv tokens and record's params,
used by DetkModuleJSON and detk-util record; module_schema.json's argv
description says absolute paths are written relative to workdir; a test
running detk-stats and detk-util record with absolute typed paths
(including `--report-dir`) that asserts `_assert_no_machine_paths` on the
module JSON, payload and crate. Belongs in release/report-paths (PR #134)
before it merges; schema stays 1.2 (not yet released). Revisit if a
consumer needs the literal command line (it could be kept, hashed, or
behind an opt-in flag).

A residual, under every option: when the report directory lies in
another tree from the working directory, `workdir` is a `../` chain that
names the working directory's path components (e.g.
`../../home/<user>/proj`), relative but revealing. Inherent to DETK-0280's
relative scheme; noted, no change proposed.
