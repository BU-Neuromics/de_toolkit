---
kind: step
time: 2026-11-20T19:38:33Z
by: DETK/reviewer
node: release/record
step: s2
branch: review/record
verdict: approve
commits: []
decisions: []
---

# Approved: Review the refusals and exit codes against DETK-0031 and DETK-0061, the module JSON and the crate (instrument, object, result, lineage into a later detk-de run), and the help from an agent's side

## Summary

Approved at d64afc4: refusals exit 1 with no module JSON, usage errors exit 2; module JSON schema 1.1 with SHA-256, 1.0 fixtures still validate; crate instrument = external tool, lineage into detk-filter and (R job, ran) detk-de; CI green incl. R. Non-blocking: PR conflicts with main in tests/cli/cli_cases.py (s3 merges main).

## Artifacts

## Findings

Review of s2 at d64afc4. Approved.

Checked: the diff f3a014f..d64afc4 (util.py, common.py, de.py, crate.py, report.py, report_specs.py, module_schema.json, tests, completions). PR #106 CI is green on d64afc4. In "test with R (bioconda)" (2227 passed, 22 skipped), tests/util/test_record.py ran all 28 tests and skipped none, so test_lineage_into_detk_de ran. The 3.11/3.12/3.13, docs-strict and runtime-only jobs are green too. Locally on 3.13 (uv, dev group), the full suite gives 2165 passed, 81 skipped; tests/util, tests/cli and tests/report give 1810 passed.

Refusals against DETK-0031 and DETK-0061 item 2, run by hand. Each exit 1 leaves no detk_report/json and no crate:
- a missing input: exit 1, "input file nope.csv does not exist", and the command does not run
- `false`: exit 1, "command failed with exit status 1: false"; the command's own status is not passed through
- a command that isn't found: exit 1, "command not found: nosuchcmd"
- a file that isn't executable: exit 1, "could not be run: Permission denied"
- killed by a signal: exit 1, "command was killed by signal 9: sh -c 'kill -9 $$'"
- an output missing after the run: exit 1, naming the file and the command
- usage errors exit 2 with the usage: no command, or `--` with nothing after it; no -o; a stray word before `--` (the message says the command goes after --); an unknown option before `--`

The module JSON (name record, schema_version 1.1) matches item 4. params holds command (shlex-joined), argv, tool, tool_version (probed: "Python 3.13.15"), inputs and outputs. properties holds the path, sha256 and size of each file, plus exit_status. in_file_path and out_file_path are the first of each list, and in_file_paths and out_file_paths are written only by record. A whole-line redirect (`... -- python3 -c ... > out.csv`) captures only the command's output: the banner and log lines go to stderr.

Schema: in_file_paths and out_file_paths are optional arrays of strings, and MODULE_SCHEMA_VERSION goes 1.0 -> 1.1. Old 1.0 documents still validate: the docs/example report's embedded documents (schema 1.0, detk 0.9.12) and the crate tests' shape, which are the only module JSON fixtures in the repository. The test_every_fixture_document_still_validates test checks them. Other modules' documents gain no new keys (pinned).

The crate matches item 5. The instrument is a SoftwareApplication #tool-<tool>-<version> with name and softwareVersion. The action is named "python3 run (recorded by detk-util record)". object lists every input plus one PropertyValue per params key, command among them. result lists every output. Each File carries sha256 and contentSize, a producer's digest wins, and the workflow-run context is added only when a sha256 is present, so crates without a record keep their context (pinned). Lineage tests: record -> detk-filter runs in every job, and record -> detk-de (DETK-0161's column_data_path) runs in the R job. Both find the recorded step as covs.csv's producer.

The report has a "Recorded external step" card with a raw view in the util family, and detk-report generate builds (pinned).

Help, read as an agent would use it: the description gives the run rules, the refusals, how the tool and version are found, and that record writes nothing to stdout. The usage line shows `-- <command> [<arg>...]`. NAME and TEXT are added to METAVARS. Both examples parse in the help test.

The parse_cli change (DETK-0160) is opt-in through command_dest. Every other parser still refuses `--` as before (test_cli_behaviours pins this).

Not blocking (for s3 or later):
1. The PR conflicts with main: a trial merge conflicts in tests/cli/cli_cases.py (main gained #103 and #105). s3 must merge main before s4.
2. The version probe runs `<argv[0]> --version`. For a user's own script (`./derive.py ...`), that runs the script a second time with --version. The help says so, and DETK-0061 item 3 decides it. docs/tools/util.md should advise --tool-version for your own scripts.
3. A stale output passes the after-run check: an --output that existed before the run is recorded even if the command didn't write it. With the whole-line redirect in example 1, the shell creates the file first, so the check can't fail there. This is as DETK-0061 decides ("must exist"). The docs could say "exist", not "written".
4. record's help lists the common option -d/--out-delim, which does nothing for record. This comes from add_common_options and affects other subcommands too. Not this node's to fix.

## Questions
