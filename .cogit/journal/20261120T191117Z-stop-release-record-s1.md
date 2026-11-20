---
kind: stop
time: 2026-11-20T19:11:17Z
by: adamlabadorf
node: release/record
branch: node/102-record
---

# release/record stop note: s1 done, PR #106 green; DETK-0160 and DETK-0161 Proposed

## Done

s1: detk-util record built as DETK-0061 decides (parser/help, run without a shell, refusals exit 1 with no module JSON, module JSON with SHA-256, schema 1.1 optional in_file_paths/out_file_paths, crate instrument = external tool, report entry without a view), cli-pin rows, tests/util/test_record.py, completion regenerated; PR #106, CI green on d8b9a08 including R

## Stopped because

the acceptance needs '-- <command>' through common.parse_cli (DETK-0160) and DETK-0061's lineage into detk-de needs de.py to pass column_data_path (DETK-0161, found by the R job); both files are outside the node's scope

## Next

driver answers DETK-0160 and DETK-0161; then s2 @reviewer; then s3 (docs/tools/util.md, commands.md, CHANGELOG incl. METAVARS NAME/TEXT and detk-de column_data_path, docs/report.md schema 1.1 if DETK-0160 is accepted)

## Open questions

-d/--out-delim is accepted by record but has no effect (kept for uniform common options)
