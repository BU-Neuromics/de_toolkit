---
template: adr
state: Accepted
authority: [human]
date: 2026-11-23
applies: [release/record-space-paths]
revisions:
  - {date: 2026-11-23, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A. Accepted under Adam's delegation via the driver session, 2026-11-20 (DETK-0063): within the 1.0 scope and does not change the 1.0 promise. Implemented in release/record-space-paths before release/cut."}
---

# An existing absolute path with whitespace in a recorded command line

## Background

DETK-0580 (Accepted, Option A; implemented in release/cli-docs, #163)
made `relative_arg` in `de_toolkit/report.py` treat an argument as an
absolute path only when it starts with `/`, has no whitespace, and its
parent directory exists. Then an awk program, a regular expression or an
`sh -c` script that starts with `/` is recorded as typed. In the s2
re-review of #163 the reviewer (who proposed that rule) found its cost: a
real absolute path with whitespace in it is now kept absolute in the
recorded `argv`, where before DETK-0580 it was written relative to
`workdir`. Run in `.../proj2`,

    detk-util record -i "$PWD/My Data/c.csv" -o g.csv -- cp "$PWD/My Data/c.csv" g.csv

records `argv` `... cp /…/proj2/My Data/c.csv g.csv`, with the absolute
path. The `-i`/`-o` lists (`in_file_paths`, params `inputs`) are not
affected: they go through `_file_relpath`, not `relative_arg`. The
recorded line still re-runs, but the report directory is no longer
relocatable for that step, and the absolute path exposes the user's
directories. docs/report.md states the whitespace rule, so this is
documented; it is not a re-run bug.

## Context

- DETK-0281: no recorded path is absolute, so a report directory can be
  moved or published as it is. DETK-0580 traded part of that away to stop
  recording a command that never ran.
- Paths with spaces are common on macOS and Windows-mounted volumes
  ("My Data", "Google Drive").
- `relative_arg` runs after the command ran, so an output path exists by
  then. An existence check is therefore exact for real files and folders,
  and a script such as `/usr/bin/env echo hi` or `/^gene/ {print}` names
  no existing file.

## Options

**A. Refine the rule in a small follow-up before release/cut.** An
argument is a path when it exists (`os.path.lexists`, whitespace or not),
or when it has no whitespace and its parent directory exists (DETK-0580's
rule, kept for a path not written). Add tests: the `My Data` case is made
relative; DETK-0580's awk, regex and `sh -c` cases are still kept;
docs/report.md's bullet and the CHANGELOG get one sentence. Cost: a few
lines; one more node before the cut.

**B. Leave it for 1.0.1.** 1.0 records such paths absolute, as documented.
Cost: 1.0 reports with spaced paths aren't relocatable, and the fix later
changes recorded output (a bug fix under semver).

**C. Leave it.** Accept that the documented whitespace rule is the 1.0
behaviour for good.

## Decision

Recommended: **A**. It restores DETK-0281's guarantee for real files
without giving back any of DETK-0580's protection, since a script or
pattern that names no existing file is still kept. It is small enough to
land before the cut. It does not block release/cli-docs: that node
implements DETK-0580 as accepted, and its docs describe what the code
does.

## Consequences

- A follow-up task node (e.g. release/record-spaced-paths) after
  release/cli-docs and before release/cut, scoped to `de_toolkit/report.py`
  (`_is_path`), `tests/report/test_report_paths.py`, docs/report.md and
  the CHANGELOG.
- A script that happens to be the exact name of an existing file is taken
  for a path. That is no worse than before DETK-0580.
