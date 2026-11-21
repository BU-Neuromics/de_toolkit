---
kind: task
objective: Each report directory holds its own Process Run Crate, and the paths recorded in module JSON and the crate are relative to the report directory, so no absolute machine path is written for a run given relative paths (DETK-0280; Adam, 2026-11-20)
acceptance:
  - 'as DETK-0280 is answered (recommended Option A): every write of the report writes ro-crate-metadata.json into the report directory, rooted there; two runs in one directory with --report-dir a and --report-dir b each leave a crate in their own directory listing only their own steps, and neither writes ./ro-crate-metadata.json; detk-report clean removes the report directory with its crate and leaves a ./ro-crate-metadata.json from an earlier run alone; a test for each'
  - module JSON records workdir relative to the report directory (.. for the default ./detk_report), argv[0] as the command's name and in_file_path, out_file_path, column_data_path, in_file_paths and out_file_paths relative to workdir (an absolute path typed on the command line is written relative too); the crate's File @ids are relative to the crate root, with no file:// URI for a local file; a test runs detk commands with a report directory inside and one outside the working directory and asserts that neither the module JSON, the embedded report payload nor the crate holds the working directory's absolute path, the home directory or the interpreter's path
  - the crate validates under the process-run-crate profile at REQUIRED level with rocrate-validator (test_crate_validates_against_profile, rooted in the report directory with ../ references), and test_file_outside_root_uses_absolute_uri is replaced by its relative counterpart; module_schema.json's workdir, argv and path descriptions say what they are relative to (the schema version bumped if the developer judges the meaning changed, per DETK-0280)
  - docs/report.md (the crate section and the schema table) says the crate is written into the report directory and what every recorded path is relative to; detk-report clean's help, docs/tools/util.md, skills/detk/SKILL.md, docs/agent-skills.md, docs/tutorials/quantifiers.md (its crate grep, still passing under the harness) and the tests that look for ./ro-crate-metadata.json follow; CHANGELOG under Changed says where the crate now is and that clean leaves an old ./ro-crate-metadata.json
from: [DETK-0280]
scope: [+de_toolkit/crate.py, +de_toolkit/report.py, +de_toolkit/util.py, +de_toolkit/module_schema.json, tests/report/test_crate.py, +tests/report/test_report.py, new:tests/report/test_report_paths.py, +tests/util/test_tidy.py, +tests/util/test_record.py, +tests/example/test_airway_example.py, +tests/cli/test_cli_help.py, +docs/report.md, +docs/tools/util.md, +docs/agent-skills.md, +docs/tutorials/quantifiers.md, +skills/detk/SKILL.md, +skills/detk/references/airway.md, +skills/detk/references/commands.md, +examples/airway/run.sh, +examples/airway/README.md, +CHANGELOG]
prev: [DETK-0280]
issue: 133
visited: 73b7582
---

# The crate goes with its report and recorded paths are relative

## Implementation plan

- [ ] @developer As DETK-0280 is answered: write the crate into the report directory, rooted there; record workdir, argv[0] and the file paths relative as it says; the crate's references relative to its root; tests for two report directories, clean, the absence of machine paths and profile conformance; the docs, skill, tutorial and tests that name ./ro-crate-metadata.json; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: in one directory run two detk commands with --report-dir a and --report-dir b, read both crates and grep both reports and crates for the directory's absolute path and $HOME; run the quantifiers tutorial; check the crate with rocrate-validator <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-21 from the release/tidy-output review (#119, not
blocking): `DetkReport` roots the crate at `os.getcwd()`
(`report.py`, about line 288), so two runs with different `--report-dir`
values in one directory overwrite each other's `./ro-crate-metadata.json`.
docs/report.md documents that location, so the change of place is
DETK-0280's (Proposed, recommending Option A: the crate goes into the
report directory).

Adam decided on 2026-11-20 that the absolute machine paths in the
published example (docs/example/) go before 1.0, fixed at the source.
They are the module JSON's `workdir` (absolute, from `os.getcwd()` in
`report.py` and the `workdir=os.getcwd()` calls in `util.py`) and
`argv[0]` (the absolute path of the installed command); the crate itself
holds none today only because the example's files lie under its root.
This node fixes the source; release/example-paths regenerates the
published example after release/tutorial-airway and
release/outlier-entropy, which both change it, and adds the test on
docs/example/.

Highest priority: ready as soon as DETK-0280 is answered. No node in
progress touches `crate.py` or `report.py`. Its `+` entries on
`examples/airway/`, `tests/example/` and `skills/detk/references/airway.md`
are the one-line crate-path changes in files release/tutorial-airway
(#117, in progress) rewrites or retires; whichever merges second merges
main and keeps the other's change (if the tutorial has retired run.sh,
there is nothing to carry). The `+` entries on `tests/util/` and
`docs/tools/util.md` share files with release/record-help, for different
lines. Before release/example-paths, release/cli-docs and release/cut.
