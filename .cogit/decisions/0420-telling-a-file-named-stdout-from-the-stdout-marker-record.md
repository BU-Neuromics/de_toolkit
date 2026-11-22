---
template: adr
state: Proposed
authority: [human]
date: 2026-11-22
from: {node: release/crate-stdout, step: s1}
applies: [release/crate-stdout]
issue: 150
---

# Telling a file named stdout from the stdout marker: record it ./stdout in module JSON

## Background

Every detk command that writes a table takes `-o FILE` with the default
`stdout`, and the value `stdout` means "write to standard output", not a
file. Module JSON records it as `out_file_path: "stdout"`, the documented
marker, and release/crate-stdout makes the Process Run Crate leave it out
(the crate named a File `../stdout` that does not exist).

The node's acceptance asks that a file the user really named `stdout`
(`-o ./stdout`, since `-o stdout` is the marker) still be listed. But module
JSON does not keep `./stdout`: `report._file_relpath` normalizes every file
path relative to `workdir` (DETK-0280), so `./stdout`, `sub/../stdout` and
`/work/stdout` are all recorded `"stdout"`, the same string as the marker.
An absolute `-o /work/stdout` is also written `-o stdout` in `argv`
(DETK-0281), which would re-run as "write to stdout". Reproduced on main at
501927d: `detk-norm cpm -o ./stdout c.csv` records `out_file_path:
"stdout"`.

## Context

The node's scope is `crate.py`, its tests and the CHANGELOG; crate.py alone
reads only what module JSON holds. Criteria: (1) the crate lists a file
exactly when a file was written; (2) module JSON keeps `stdout` as the
marker (acceptance); (3) the recorded `argv` re-runs as typed (DETK-0281);
(4) the smallest change, no new schema field, within the 1.0 promise.

## Options

1. **Record a file named stdout as `./stdout`** (report.py, one line in
   `_file_relpath`): the literal `stdout` is kept as the marker; any other
   spelling that resolves to `<workdir>/stdout` is written `./stdout`.
   crate.py skips exactly `stdout`. Meets 1-4: `./stdout` is still a path
   relative to `workdir`, as the schema says; it also fixes the absolute
   `-o /work/stdout` in `argv`. Touches `de_toolkit/report.py`, outside the
   node's declared scope. Reports already written keep `stdout` for such a
   file and lose it from the crate when regenerated (pre-1.0 data, a file
   named stdout: rare).
2. **crate.py reads `argv`**: `stdout` is a real file when an argv token
   (or the value of `--output=`/`-o`) spells it otherwise. Within scope, but
   parses the command line heuristically and fails for an absolute path,
   which `argv` already records as `stdout` (criteria 1, 3).
3. **crate.py checks the disk**: `stdout` is a file when `<workdir>/stdout`
   exists when the crate is built. Within scope, but wrong when the file is
   later removed, or one exists from an earlier step (criterion 1).
4. **Drop the requirement**: never list a file named `stdout`. Narrows the
   node's acceptance; the human's.

`detk-util record` is apart in every option: its outputs are files it
checked exist and checksummed, so a recorded output `stdout` is always a
File.

## Decision

Recommended: option 1. The ambiguity is made when the path is recorded, so
it is resolved there, in one line, keeping the marker as documented, and it
fixes the recorded command line too. It widens the node's scope by
`de_toolkit/report.py` (implemented on PR for #147 in the same commit; option
2 is the fallback if the scope must not grow).

## Consequences

- module JSON writes `./stdout` (not `stdout`) for a file in `workdir`
  named stdout, in `out_file_path`, `out_file_paths`, record's
  params/properties and an absolute `argv` path; no schema change.
- crate.py's rule is simple: `out_file_path(s)` equal to `stdout` is no
  file, except for record.
- Revisit if a tool ever needs `stdout` as an input marker, or `-` as an
  output (it is kept by `_file_relpath` but not yet left out of the crate).
