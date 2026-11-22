---
template: adr
state: Accepted
authority: [human]
date: 2026-11-21
from: {node: release}
applies: [release, release/report-paths]
issue: 128
revisions:
  - {date: 2026-11-21, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20 (DETK-0063): Option A, the crate goes into the report directory, rooted there, and recorded paths are relative to it; carries out Adam's 2026-11-20 instruction to make the paths relative and stays within the 1.0 scope"}
---

# Where the Process Run Crate is written and what recorded paths are relative to

- Proposed by: the planning session (plan/followups-6), 2026-11-21

## Background

Every detk command that writes to the report also leaves a module JSON
document under `<report-dir>/json/`. From those documents detk builds two
things: the HTML report (`<report-dir>/detk_report.html`, which embeds the
documents) and a provenance file, the Process Run Crate
(`ro-crate-metadata.json`, an RO-Crate in JSON-LD).

Today the crate is always written to the current working directory, and
that directory is the crate's root: a file the tools read or wrote is
named by its path relative to the working directory, or by an absolute
`file://` URI when it lies outside it (`crate.py`, `_file_ref`). The
module JSON records `workdir` as the absolute working directory and
`argv` as `sys.argv`, whose first entry is the absolute path of the
installed command. docs/report.md says the crate is written "at the
analysis working directory".

## Context

- **The bug (#119 review).** Two runs in one directory with different
  `--report-dir` values each rewrite `./ro-crate-metadata.json` from
  their own report's JSON only, so the second run's crate replaces the
  first's, and neither report's crate survives beside it.
- **Adam's decision of 2026-11-20.** The published example report and
  crate (`docs/example/`) must hold no absolute machine paths before 1.0.
  Today the report embeds `"workdir": "/home/.../examples/airway"` twelve
  times and `"argv": ["/home/.../.venv/bin/detk-stats", ...]`. He asked
  for the fix at the source: paths recorded in reports and crates
  relative to the report and crate location.
- The crate root must be the directory that holds
  `ro-crate-metadata.json` (RO-Crate 1.1). Where the crate goes therefore
  fixes what its file references are relative to.
- The published example already treats the report and the crate as one
  unit: `docs/example/` holds `detk_report.html` beside
  `ro-crate-metadata.json`.
- RO-Crate 1.1 expects data entities inside the crate root or as absolute
  URIs. rocrate-validator 0.11.3 (the version in the lock) accepts a crate
  whose File entities are `../counts.csv` with no REQUIRED issue under the
  process-run-crate profile (checked by the planning session on main at
  61bf890); its RECOMMENDED issues are the same as today's.
- Criteria: each report keeps its own crate; no absolute path from the
  machine in a report or crate built from relative command lines; the
  crate stays valid under the profile at REQUIRED level; little machinery.
  Within DETK-0063: the crate's location is a documented output, not part
  of the CLI promise of DETK-0001/DETK-0025, and 1.0 is where it can move.

## Options

### Option A: the crate goes with the report, rooted there (recommended)

`ro-crate-metadata.json` is written to `<report-dir>/`, and the report
directory is its root. File references are relative to the report
directory (`../counts.csv` for the default `./detk_report`). The module
JSON records `workdir` relative to the report directory (`..` by
default), `argv[0]` as the command's name (`detk-stats`), and the file
path fields relative to `workdir` (a path typed as absolute is written
relative to it); the rest of `argv` is kept as typed. `detk-report clean`
removes the report directory, and the crate with it.

- Each report has its own crate; two report directories never collide.
- A report directory is self-contained: copied or published, as
  `docs/example/` is, its crate travels with it and its references
  resolve from where it sits.
- References outside the root (`../`) are outside RO-Crate 1.1's
  expectation, though the validator accepts them at REQUIRED level.

### Option B: the crate stays in the working directory and covers every report there

The crate root stays the working directory, as documented. On each
write, detk rebuilds `./ro-crate-metadata.json` from the module JSON of
every report directory recorded from that working directory (kept as a
list in the crate, or found by scanning).

- File references stay inside the root, as RO-Crate expects.
- The bookkeeping is new and fragile: deleted or moved report
  directories, a report directory outside the working directory, and
  `detk-report generate` run from elsewhere all need rules. A published
  report directory still has no crate of its own.

### Option C: keep the crate where it is and refuse to overwrite another report's crate

The crate stays at the working directory; detk records which report
directory built it and, when another one would replace it, warns and
writes nothing (or fails).

- Smallest change, and the documented contract holds.
- It fixes the overwrite by dropping the second report's provenance,
  which is the loss the bug report is about.

## Decision

Recommended: Option A. It removes the collision by construction, makes
each report directory a self-contained unit (which is how docs/example
already publishes it), and gives one place, the report directory, that
every recorded path is relative to, as Adam asked. The cost, `../`
references, passes the profile at REQUIRED level today.

## Consequences

- release/report-paths implements it: crate.py, report.py, the schema's
  field descriptions, docs/report.md and every page or test that names
  `./ro-crate-metadata.json`; the CHANGELOG says where the crate now is.
- An existing `./ro-crate-metadata.json` from an earlier run is left
  alone; `detk-report clean` no longer removes it (the CHANGELOG says so).
- A consumer that read `workdir` as an absolute path must resolve it
  against the report directory. The schema version goes to 1.2 if the
  developer finds the field's meaning changed under the envelope's rule;
  that is the developer's call within this record.
- Revisit if rocrate-validator, or a profile update, rejects `../`
  references at REQUIRED level: the fallback is Option B.
