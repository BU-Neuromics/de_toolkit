---
kind: step
time: 2026-11-20T19:43:01Z
by: DETK/developer
node: release/record
step: s3
branch: node/102-record
verdict: done
commits: [e06ffed, afdd389]
decisions: []
---

# Done: Wire it into the umbrella command and completion, document it in docs/tools/util.md and the skill's commands.md, CHANGELOG

## Summary

Merged origin/main (cli_cases.py conflict: main's BOOL token kept with record's required/repeat handling; completions unchanged). docs/tools/util.md record section with the s2 reviewer's notes 2 and 3 (an output that existed before the run, e.g. from a shell redirect, passes the check; give --tool-version for your own script since the version check runs it with --version), also in --help; skill commands.md usage block (DETK-0010 test passes) with note and example; docs/report.md schema 1.1 and the optional lists (DETK-0160); CHANGELOG: record, schema 1.1, NAME/TEXT metavars, detk-de column_data_path (DETK-0161). Umbrella and completion were wired in s1. Full suite, ruff and mkdocs --strict pass locally. Note 4 (-d on record) left out of scope.

## Artifacts

## Findings

## Questions
