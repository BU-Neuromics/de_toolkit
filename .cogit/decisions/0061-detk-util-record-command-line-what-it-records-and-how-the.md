---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release}
applies: [release/record]
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20: accepted on the planning session's recommendation (the first option of each item); within the scope Adam set and no change to the 1.0 promise"}
---

# detk-util record: command line, what it records and how the crate shows it

- Proposed by: the planning session, 2026-11-20, for the design details
  DETK-0051 leaves open. Within the 1.0 definition of done and the scope
  Adam set (DETK-0051 item 3), so it may be accepted under his
  delegation (DETK-0063).

## Background

Adam chose to document Miller for derived covariates and to add one
detk command, `detk-util record`, that runs an external command and
records it in detk's provenance (DETK-0051, Option C). A step outside
detk otherwise leaves a gap: a `detk-de` run would show its column data
as a file no step produced. `record` closes that gap for any external
tool (Miller, awk, an R script). It is part of the 1.0 CLI, so its
options and what it writes are promised until 2.0 (DETK-0025).

## Context

- **The module JSON envelope** (`de_toolkit/module_schema.json`, schema
  1.x) has one `in_file_path`, one `column_data_path`, one
  `out_file_path`, plus `params`, `properties`, `argv` and times. Its
  `id` hashes the module name, `params`, the input path and detk's
  version.
- **The crate** (`crate.py`) makes one `CreateAction` per document: its
  `instrument` is a `SoftwareApplication` for the detk command
  (`SUBTOOLS` maps the module name to it), `object` the input and column
  data files plus one `PropertyValue` per `params` key, `result` the
  output file. Lineage between steps comes from shared file paths.
- **Exit codes** are 0 success, 2 usage error, 1 anything else
  (DETK-0031). Help follows DETK-0025 Option B, with a tested example
  per subcommand.
- **Typical use** is a command that writes a file, either itself (the
  Miller recipes write with `emit > "file"`, DETK-0062) or on stdout
  through a shell redirect:
  `detk-util record -i a.csv -o b.csv -- awk -F, '...' a.csv > b.csv`.
- **Criteria:** the step is traceable in the crate as the producer of
  its outputs; nothing silent (a failed command records nothing); small
  enough to promise; no new dependency.

## Options

Each item is a separate choice. The recommendation comes first; the
alternatives follow it.

### 1. Command line

**Recommended:**
`detk-util record [options] -i FILE... -o FILE... -- <command> [<arg>...]`

- `-i FILE --input=FILE` (repeatable): an input file. Zero or more.
- `-o FILE --output=FILE` (repeatable): an output file. At least one:
  the point of recording is the lineage of a file.
- `--tool=NAME`: the tool's name, default the basename of the first word
  of the command (`mlr`). Needed when the command is `sh -c '...'` or
  `Rscript script.R`.
- `--tool-version=TEXT`: the version to record instead of asking the
  tool (item 3).
- `--report-dir=DIR` as on every other command.
- Everything after `--` is the command, run as given, without a shell.
  A pipeline or a redirect inside the step needs `sh -c '...'`.

`-o` keeps detk's meaning, "a file this step writes", though here the
external command writes it, not detk.

Alternatives: (a) `--in`/`--out` as the research sketched (no short
forms, and `--in` reads oddly); (b) taking inputs and outputs from the
command line by parsing it, which cannot work for arbitrary tools.

### 2. Running the command

**Recommended:** run the command with detk's stdin, stdout and stderr
inherited, so a redirect of `detk-util record ...` is the command's own
output (`... > out.csv` works), and `record` writes nothing to stdout
itself (its messages go to stderr). Before running, every `--input` must
exist (exit 1 naming it). After a zero exit, every `--output` must exist
(exit 1 naming the missing one, and no module JSON). If the command
exits non-zero, `record` writes no module JSON and exits 1, saying on
stderr which command failed and with what status. A command that is not
found is exit 1. `record` never deletes or rewrites a file.

Alternatives: (a) pass the command's own non-zero status through
(handy in scripts, but it breaks DETK-0031's one meaning for 1, and a
command may itself exit 2); (b) a `--stdout FILE` option instead of
the shell redirect (more to promise, and a redirect is what users
write).

### 3. The tool's version

**Recommended:** unless `--tool-version` is given, run
`<tool-executable> --version` with a 10 s timeout and record the first
non-empty line of its output. If that fails or times out, record
`unknown` and warn on stderr; it is not an error, because some tools
have no `--version`. With `--tool` and a `sh -c` command, the version
is `unknown` unless given.

Alternative: make a missing version an error (safer for provenance, but
it fails on tools without `--version`).

### 4. What the module JSON holds

**Recommended:** the module is named `record`. The envelope's
`in_file_path` is the first input (or null), `out_file_path` the first
output, `column_data_path` null. `params` holds `command` (the command
as one shell-quoted string, for reading), `argv` (the list, for
re-running), `tool`, `tool_version`, `inputs` and `outputs` (the
lists, as given). `properties` holds the SHA-256 and size of every
input (read before the run) and output (read after), and the exit
status. The checksums tie the record to the exact files, so a reader
can tell whether a file was changed after it was recorded.

The envelope gains two optional fields, `in_file_paths` and
`out_file_paths` (lists), written by `record` and read by the crate, so
a step with several inputs or outputs links them all. Both are
optional, so every document detk wrote before stays valid; the
schema's minor version goes up.

Alternatives: (a) keep the extra files in `params` only (no schema
change, but the crate would link only the first input and output); (b)
no checksums (smaller documents, weaker provenance).

### 5. How the crate shows it

**Recommended:** the step's `CreateAction` has as `instrument` a
`SoftwareApplication` for the external tool (`name` the tool,
`softwareVersion` its version), because that is the software that
made the file. The action's `name` says it was recorded:
`mlr run (recorded by detk-util record)`. Its `object` holds every
input and the `PropertyValue`s of `params` (the command among them),
and `result` every output, with their checksums as each file's
`sha256`. `SUBTOOLS` gets `"record": ("detk-util", "record")` for the
label, and `crate.py` takes the instrument from `params` for this
module. A later `detk-de` run that reads the recorded output as column
data then shows the recorded step as its producer.

Alternative: the instrument is `detk-util record` and the tool is a
`PropertyValue` (simpler code, but the crate then says detk made a
file Miller made).

### 6. Report view

**Recommended: none in 1.0.** The report lists the step in its run
order like other modules without a view, showing the command, the tool
and its version; a fuller view can come in a 1.x minor release. (This
also matches one reading of Adam's "no need for the report here",
DETK-0051 item 5.)

Alternative: a view with the files and checksums now.

## Decision

Proposed. The planning session recommends the first option of each
item and that it be accepted under Adam's delegation (DETK-0063): it
stays inside the scope Adam set in DETK-0051 and adds nothing to the
1.0 promise beyond the subcommand he asked for.

## Consequences

release/record builds `record` as decided: parser and help on the
cli-migrate pattern with a tested example, the exit codes of DETK-0031,
completion (DETK-0032), a cli-pin table, the schema's optional fields
and their validation test, the crate's instrument and file links, and
tests that record a real external command (a Python one-liner, so the
tests need no Miller) and check the module JSON and the crate.
