---
kind: task
objective: 'detk-util record runs an external command (Miller, awk, an R script) and records it as a detk step, so a file it makes shows in the module JSON and the Process Run Crate as the output of a step (DETK-0051 Option C, DETK-0061)'
acceptance:
  - 'detk-util record takes the command line DETK-0061 decides (repeatable --input and --output, --tool, --tool-version, --report-dir, the command after --), runs the command without a shell with stdio inherited, and refuses as it decides: a missing input, a missing output after the run, a failed or missing command each exit 1 with a message naming it and write no module JSON (DETK-0031)'
  - 'the module JSON (name record) holds the command, argv, tool, tool version, inputs and outputs in params and each file''s SHA-256 and size in properties; the envelope''s optional in_file_paths and out_file_paths validate against module_schema.json, whose minor version goes up, and every module JSON a test fixture holds still validates'
  - 'the crate makes the step a CreateAction whose instrument is the external tool with its version, whose object and result list every input and output, and whose command is a PropertyValue; a test records a command that writes a column data file, runs a detk step on it, and finds the recorded step as that file''s producer in the crate'
  - 'the report lists a record step without a view (DETK-0061 item 6) and builds without error'
  - 'its parser and help follow the release/cli-migrate pattern and DETK-0025 Option B with an example the help test parses; it is in the umbrella detk command, the completion scripts (DETK-0032) and a cli-pin table'
  - 'tests use a Python one-liner as the external command, so they need no Miller; docs/tools/util.md documents it; the skill''s commands.md usage block passes DETK-0010''s test; CHANGELOG'
from: [DETK-0051, DETK-0061]
scope: [tests/util/, tests/cli/, de_toolkit/completions/, +de_toolkit/util.py, +de_toolkit/crate.py, +de_toolkit/report.py, +de_toolkit/report_specs.py, +de_toolkit/module_schema.json, +docs/tools/util.md, +skills/detk/references/commands.md, +CHANGELOG]
prev: [DETK-0051, DETK-0061, release/cli-gaps]
---

# Record an external step with detk-util record

## Implementation plan

- [ ] @developer Build `detk-util record` as DETK-0061 decides (parser and help on the cli-migrate pattern, running the command, the checks, the module JSON with checksums, the schema's optional fields, the crate's instrument and file links, the report entry without a view), with unit, cli-pin, help and crate-lineage tests; open the PR <!-- s1 -->
- [ ] @reviewer Review the refusals and exit codes against DETK-0031 and DETK-0061, the module JSON and the crate (instrument, object, result, lineage into a later detk-de run), and the help from an agent's side <!-- s2 -->
- [ ] @developer Wire it into the umbrella command and completion, document it in docs/tools/util.md and the skill's commands.md, CHANGELOG <!-- s3 -->
- [ ] @reviewer Review the PR, CI and the docs build <!-- s4 -->
- [ ] @human Accept <!-- s5 -->

## Notes

Planned 2026-11-19 as release/augment (a detk-augment command); replanned
2026-11-20 when Adam answered DETK-0051 with Option C: "go with c, and I like
the record command". The Miller recipes that use this command are
release/miller-recipes. Comes after release/cli-gaps so it is born with the
final exit codes and completion. Waits on DETK-0061 (Proposed; recommended
for acceptance under Adam's delegation, DETK-0063).
