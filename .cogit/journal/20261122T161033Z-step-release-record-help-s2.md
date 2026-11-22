---
kind: step
time: 2026-11-22T16:10:33Z
by: DETK/reviewer
node: release/record-help
step: s2
branch: node/135-record-help
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: read detk-util record --help as a new user, and check -d is gone there and still on detk-util tidy and another command

## Summary

Approved: record's help says plainly that the version probe runs the command once more and why; -d/--out-delim refused on record and kept on every other command; CI green including R

## Artifacts

## Findings

- Read `detk-util record --help` as a new user. The new paragraph ("Without --tool-version, record runs '<command> --version' once to read the version, so a script that ignores --version would run its whole step a second time: give --tool-version for your own scripts (./derive.py).") says plainly who runs what and why it matters. The same wording is in docs/tools/util.md (tip) and skills/detk/references/commands.md. test_record_help_says_the_version_probe_runs_the_command_once_more asserts it.
- -d/--out-delim: gone from record's help (both the options list and the completions). `record -d , ...` and `record --out-delim=, ...` exit 2 with "unrecognized arguments". Still listed on detk-util tidy, detk-norm deseq2, detk-filter and detk-stats summary. --report-dir, --no-report, --version, -v, -q and --shut-up stay on record. New Bad rows in cli_tables, plus Sub.without_common and a parametrized help test that checks each common option is listed or left out as declared.
- `--out` on record now resolves to `--output` instead of being ambiguous. This is intended: prefix matching is on by design (argparse allow_abbrev, kept from docopt per DETK-0023). With --out-delim gone, --out is a unique prefix of --output on record. test_long_option_prefix_out_is_ambiguous_and_rejected still covers the ambiguous case on deseq2, which keeps -d. No decision needed.
- The regenerated completions de_toolkit/completions/detk.{bash,zsh} are outside the listed scope but necessary: they only drop -d/--out-delim from record's two entries in each file, and tests/completion requires them to match the parsers. detk.tcsh has no per-option record entries and is unchanged.
- CHANGELOG entry under Changed is accurate.
- Checks: full suite locally 2397 passed, 142 skipped (R-gated tests skipped, no R here). ruff check and format clean. PR #139 CI is all green at 5c736d4, including "test with R (bioconda)", the docs strict build and coverage.
- Nit (non-blocking): the new paragraph partly repeats the sentence before it ("Its version is the first line of '<command> --version' ... unless --tool-version gives it"). This is acceptable because the separate paragraph is what makes the consequence stand out.

## Questions
