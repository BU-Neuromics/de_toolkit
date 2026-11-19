---
kind: task
objective: 'Every detk-* command parses its command line with argparse, with help as DETK-0025 Option B promises it, and docopt-ng is gone (DETK-0001, DETK-0023, DETK-0025)'
acceptance:
  - 'all 11 entry points (detk and detk-norm, -de, -enrich, -transform, -filter, -stats, -outlier, -wrapr, -report, -util) and their subcommands use argparse; docopt-ng is not in pyproject.toml or uv.lock, and de_toolkit/test_docopt.py is removed'
  - 'the release/cli-pin tests pass with their expectations unchanged except where this node changes them on purpose (the metavars and the umbrella command below); only their adapter changes otherwise. A pinned behaviour argparse cannot keep is a question for Adam before it is dropped, and a breaking change in the CHANGELOG once agreed'
  - 'help follows DETK-0025 Option B for every command and subcommand: the section order description, usage, positional arguments, options, common options, examples; every positional and option listed with metavar, default, choices and a one-line description; and at least one example command line per subcommand. A test checks the structure for every command and that each example parses, and runs it where test data allows'
  - 'the umbrella `detk <command>` runs every module command, enrich, report and util included, and its usage lists them all (DETK-0025 gap 1)'
  - 'option metavars follow one convention across commands (FILE for files, DIR for directories, N for numbers, as today''s majority does), including detk-filter''s `<out_fn>`, --rda and --routput-dir; the pins and the CHANGELOG record each change (DETK-0025 gap 3)'
  - 'DETK-0010''s skill test checks the skill''s command lines against the argparse parsers; DETK-0010 is superseded or revised (as cogit allows for an Accepted record) to say so; the usage blocks in skills/detk/references/commands.md match the new --help'
  - 'the full test suite, the R-gated tests in CI and ruff pass; the airway example (run.sh) runs unchanged'
from: [DETK-0001, DETK-0023, DETK-0025]
scope: [de_toolkit/common.py, de_toolkit/norm.py, de_toolkit/de.py, de_toolkit/enrich.py, de_toolkit/transform.py, de_toolkit/filter.py, de_toolkit/stats.py, de_toolkit/outlier.py, de_toolkit/wrapr.py, de_toolkit/report.py, de_toolkit/util.py, de_toolkit/test_docopt.py, tests/cli/, tests/skills/, tests/common/, tests/norm/, tests/de/, tests/enrich/, tests/transform/, tests/filter/, tests/stats/, tests/outlier/, tests/wrapr/, tests/report/, tests/util/, skills/detk/references/commands.md, pyproject.toml, uv.lock, environment.yml, +CHANGELOG]
prev: [DETK-0023, DETK-0025, release/cli-pin]
---

# Replace docopt-ng in every command

## Implementation plan

- [ ] @developer Build the shared pieces in `common.py` on argparse (the common options, the subcommand dispatch, the help sections and examples, the umbrella `detk`) and migrate `detk-norm` on them as the pattern; switch the cli-pin adapter; open the PR <!-- s1 -->
- [ ] @reviewer Review the pattern before it is copied: cli-pin passes for detk-norm, help follows DETK-0025 Option B and reads well for an agent <!-- s2 -->
- [ ] @developer Migrate the other ten entry points with examples, harmonize metavars, fix the umbrella command, move the skill test to argparse (DETK-0010), regenerate the skill's usage blocks, remove docopt-ng and `test_docopt.py`, relock, CHANGELOG <!-- s3 -->
- [ ] @reviewer Review the PR, including the R-gated tests in CI and the airway run <!-- s4 -->
- [ ] @human Accept <!-- s5 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B); argparse is
DETK-0023, help is DETK-0025 Option B (both accepted). Of the CLI gaps
Adam put in 1.0 (DETK-0025), this node fixes the umbrella command (1) and
the metavars (3), which need no further choice. `--size-factors` (2) is
release/size-factors. `--column-data` (4), exit codes (5) and shell
completion (7) are release/cli-gaps; until then, usage errors exit as
argparse does (2).

Module docstrings stay as the commands' descriptions; where they also
served as the parser spec, the spec moves into code. The tests that call
docopt today (most `tests/*/test_*.py` build their arguments with it) move
with their modules. Shares `pyproject.toml` and `uv.lock` with
release/formula-migrate and release/statsmodels-test: whichever lands
later relocks.

Updated 2026-11-19 on Adam's answers: usage errors exiting 2 is the code
DETK-0031 keeps. The deprecated `--column-data` options (detk-filter,
detk-stats summary and pca) are migrated as they are and removed by
release/cli-gaps (DETK-0030). `environment.yml` is deleted by
release/statsmodels-test (DETK-0048); its entry in the scope above stays
only for the case where this node lands first.
