---
kind: task
objective: detk-util record's --help reads unambiguously and lists only the options record uses
acceptance:
  - the --tool-version sentence in record's description says plainly that without --tool-version record runs '<command> --version' once to read the version, so a script that ignores --version would run its whole step a second time; give --tool-version for your own scripts; the same wording in docs/tools/util.md's record section and skills/detk if they carry it; a help test asserts the new sentence
  - -d/--out-delim is not listed under detk-util record --help and is refused as an unknown option there (record writes no table), while every other command keeps it; --report-dir and the other common options record does use stay; test_cli_help and the cli-pin tables updated; CHANGELOG under Changed
scope: [+de_toolkit/util.py, +de_toolkit/common.py, +tests/util/test_record.py, +tests/cli/cli_cases.py, +tests/cli/cli_tables.py, +tests/cli/test_cli_help.py, +docs/tools/util.md, +skills/detk/references/commands.md, +CHANGELOG]
prev: [release/tidy-output, release/cli-messages]
issue: 135
visited: 06c6a10
status: done
done: af3767c
---

# detk-util record's help says what it does and lists only its options

## Implementation plan

- [x] @developer Reword record's --tool-version sentence, drop -d/--out-delim from detk-util record (kept on every other command), the same in docs/tools/util.md and the skill's commands page; help tests and cli-pin rows; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: read detk-util record --help as a new user, and check -d is gone there and still on detk-util tidy and another command <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 from the release/record review (#106, reviewer note 4
and the help wording):

- The description ends "asking for the version runs '<script> --version',
  which runs a script that does not handle --version a second time": it
  reads as if record runs the script a second time, and does not say why
  that matters. The point is that the version probe runs the script once
  more, and a script that ignores --version would redo its step.
- `-d/--out-delim` comes from `add_common_options` in `common.py`, so it is
  listed on `detk-util record`, which writes no table; it has no effect
  there. record is new in 1.0, so dropping the option breaks no 0.x run.

After release/tidy-output (#119, which holds `tests/util/` and edits
`util.py`) and release/cli-messages (both edit `common.py` and the cli-pin
tables). release/cli-docs (which owns `docs/tools/`) comes after it.
Before release/cut.
