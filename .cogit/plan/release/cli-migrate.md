---
kind: task
objective: 'Every detk-* command parses its command line with the library chosen in DETK-0023, and docopt-ng is gone (DETK-0001)'
acceptance:
  - 'all 11 entry points (detk and detk-norm, -de, -enrich, -transform, -filter, -stats, -outlier, -wrapr, -report, -util) and their subcommands use the parser of DETK-0023; docopt-ng is not in pyproject.toml, uv.lock or environment.yml, and de_toolkit/test_docopt.py is removed'
  - 'the release/cli-pin tests pass with their expectations unchanged; only their adapter changes. A pinned behaviour the parser cannot keep is a decision for Adam before it is dropped, and a breaking change in the CHANGELOG once agreed'
  - '`detk-x --help` and `detk-x sub --help` describe each command, argument, option and default; a wrong command line exits non-zero naming the problem'
  - 'DETK-0010''s skill test checks the skill''s command lines against the new parser, the record revised to say so, and the usage blocks in skills/detk/references/commands.md match the new --help'
  - 'the full test suite, the R-gated tests in CI and ruff pass; the airway example (run.sh) runs unchanged'
from: [DETK-0001, DETK-0023]
scope: [de_toolkit/common.py, de_toolkit/norm.py, de_toolkit/de.py, de_toolkit/enrich.py, de_toolkit/transform.py, de_toolkit/filter.py, de_toolkit/stats.py, de_toolkit/outlier.py, de_toolkit/wrapr.py, de_toolkit/report.py, de_toolkit/util.py, de_toolkit/test_docopt.py, tests/cli/, tests/skills/, tests/common/, tests/norm/, tests/de/, tests/enrich/, tests/transform/, tests/filter/, tests/stats/, tests/outlier/, tests/wrapr/, tests/report/, tests/util/, skills/detk/references/commands.md, pyproject.toml, uv.lock, environment.yml, +CHANGELOG]
prev: [DETK-0023, release/cli-pin]
---

# Replace docopt-ng in every command

## Implementation plan

- [ ] @developer Build the shared pieces in `common.py` (the common options, the subcommand dispatch, the help text) on the DETK-0023 parser and migrate `detk-norm` on them as the pattern; switch the cli-pin adapter; open the PR <!-- s1 -->
- [ ] @reviewer Review the pattern before it is copied: cli-pin passes for detk-norm unchanged, help and errors read well for an agent <!-- s2 -->
- [ ] @developer Migrate the other ten entry points, move the skill test to the new parser (revise DETK-0010), regenerate the skill's usage blocks, remove docopt-ng and `test_docopt.py`, relock, CHANGELOG <!-- s3 -->
- [ ] @reviewer Review the PR, including the R-gated tests in CI and the airway run <!-- s4 -->
- [ ] @human Accept <!-- s5 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B); waits on his
choice of parser (DETK-0023). Module docstrings stay as the commands'
descriptions; where they also served as the parser spec, the spec moves
into code. The tests that call docopt today (most `tests/*/test_*.py`
build their arguments with it) move with their modules. Shares
`pyproject.toml`, `uv.lock` and `environment.yml` with
release/formula-migrate: whichever lands second relocks.
