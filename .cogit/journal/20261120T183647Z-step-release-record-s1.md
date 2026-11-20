---
kind: step
time: 2026-11-20T18:36:47Z
by: DETK/developer
node: release/record
step: s1
branch: node/102-record
verdict: done
commits: [69d4919]
decisions: [DETK-0160]
---

# Done: Build `detk-util record` as DETK-0061 decides (parser and help on the cli-migrate pattern, running the command, the checks, the module JSON with checksums, the schema's optional fields, the crate's instrument and file links, the report entry without a view), with unit, cli-pin, help and crate-lineage tests; open the PR

## Summary

Built detk-util record as DETK-0061 decides: parser/help on the cli-migrate pattern with two examples, run without a shell with stdio inherited, refusals exit 1 with no module JSON (missing input, command not found/not runnable/non-zero, missing output), usage errors exit 2; module JSON record with command/argv/tool/tool_version/inputs/outputs in params and SHA-256+size in properties; schema 1.1 with optional in_file_paths/out_file_paths; crate instrument = external tool + version, object/result every file, command a PropertyValue, sha256/contentSize on Files; report lists the step with no view. Tests: tests/util/test_record.py (Python one-liner; lineage into detk-filter, R-gated detk-de), cli-pin table rows (generator gains Opt.repeat/required, Pos.after_dashdash), METAVARS NAME/TEXT, completion regenerated. common.parse_cli edited to take the command after -- (outside scope): DETK-0160 Proposed. Full suite passes on 3.13; cli/util/report/completion on 3.11.

## Artifacts

## Findings

## Questions

- DETK-0160 release/record lets detk-util record take its command after --, in common.parse_cli outside its scope (#104)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
