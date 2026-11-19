---
kind: task
objective: 'A detk command adds derived columns (a constant, logs, scaling) to a column data file and records itself like every other step, so formulas can stay model-only (DETK-0050, DETK-0051)'
acceptance:
  - 'the command exists as DETK-0051 places and names it, with the operations, options, defaults and refusals it decides: a constant column; logs with base, pseudocount and zero handling; scaling by z-score (sample sd, n-1), centring and min-max to [0, 1]'
  - 'it writes a new column data file: every original column and row kept as written (IDs as text, DETK-0015), the new columns appended under the names DETK-0051 sets, a name clash refused; values match numpy/pandas references in tests, including the sample standard deviation and R''s scale() on the same data where R is available'
  - 'each run writes a module JSON document (input as column_data_path, output as out_file_path, the operation and options in params, the per-column source and numbers in properties as DETK-0051 decides) that validates against the schema; the crate maps it to its command and shows it as the producer of a later detk-de run''s column data; a report view shows the new columns'
  - 'its parser and help follow the release/cli-migrate pattern and DETK-0025 Option B (sections, metavars, at least one example per subcommand that the help test parses); it exits per DETK-0031; it is in the umbrella detk command, the regenerated completion scripts (DETK-0032) and a cli-pin table'
  - 'the formula error for a call in a formula (release/formula-rename) names this command, and docs/formulas.md says how to derive a covariate with it'
  - 'a docs page under docs/tools/ with the mkdocs nav entry, the skill''s commands.md usage block (DETK-0010''s test passes) and a short note in the skill''s design section; CHANGELOG'
  - 'an end-to-end test: augment log on the airway example''s column data, then detk-de deseq2 with the new column in the design, R-gated in CI'
from: [DETK-0050, DETK-0051]
scope: [de_toolkit/augment.py, tests/augment/, docs/tools/augment.md, tests/cli/, de_toolkit/completions/, +de_toolkit/common.py, +de_toolkit/formula.py, +de_toolkit/crate.py, +de_toolkit/report_specs.py, +pyproject.toml, +docs/tools/index.md, +mkdocs.yml, docs/formulas.md, +skills/detk/references/commands.md, +skills/detk/SKILL.md, +CHANGELOG]
prev: [DETK-0050, DETK-0051, release/formula-rename, release/cli-gaps]
---

# Column data augmentation command

## Implementation plan

- [ ] @developer Build the command DETK-0051 decides (parser and help on the cli-migrate pattern, the operations with their checks, the output file, module JSON, crate entry, report view), with unit, cli-pin and help tests; open the PR <!-- s1 -->
- [ ] @reviewer Review the operations and refusals against DETK-0051, the provenance in the module JSON and the crate, and the help from an agent's side <!-- s2 -->
- [ ] @developer Wire it into the umbrella command and completion, name it in the formula error and docs/formulas.md, add the docs page, nav, skill entries, the R-gated end-to-end test and the CHANGELOG <!-- s3 -->
- [ ] @reviewer Review the PR, including the R-gated test in CI and the docs build <!-- s4 -->
- [ ] @human Accept <!-- s5 -->

## Notes

Planned 2026-11-19, replacing release/formula-transforms (renamed here) on
Adam's change of mind (DETK-0050, superseding DETK-0028 and DETK-0047): "the
formula should just specify models, and nothing else. I wonder instead if
detk should provide some simple augmentation functions...". Waits on
DETK-0051 (name, placement, options, names, provenance), Proposed and
Adam's. The scope assumes the recommended placement, a new
`de_toolkit/augment.py` and entry point `detk-augment`; if Adam places it
under detk-util, `de_toolkit/util.py` and `tests/util/` replace those two
entries. Comes after release/cli-gaps so it is born with the final exit
codes and completion, and after release/formula-rename, whose error it
names itself in. release/cli-docs comes after it.
