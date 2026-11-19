---
kind: task
objective: 'The docs show the finished 1.0 CLI as it is, state what it promises, and are kept in step by a test (DETK-0001, DETK-0025)'
acceptance:
  - 'every usage block in docs/tools/*.md and docs/report.md matches the installed --help, and a test in CI checks it as DETK-0010''s test does for the skill'
  - 'docs/index.md and docs/api.md (where the #37 statement says the CLI is the promise) state what 1.0 promises about help, per DETK-0025 Option B: the structure, the listed facts and the examples, not the wording'
  - 'the exit codes are documented as 0 success, 2 usage error, 1 anything else (DETK-0031), on docs/concepts.md; how to enable bash, zsh and tcsh completion from the shipped scripts is documented (DETK-0032); detk-filter''s usage shows no --column-data (DETK-0030)'
  - 'no page describes command lines as built from docopt docstrings; docs/dev/ says how to add a command or option with argparse, including its help example'
  - 'the README, quickstart and example commands run as written on the migrated CLI'
  - 'uv run --group docs mkdocs build --strict passes'
from: [DETK-0001, DETK-0025, DETK-0031, DETK-0032]
scope: [docs/tools/, docs/report.md, docs/index.md, docs/quickstart.md, docs/concepts.md, docs/api.md, docs/agent-skills.md, docs/example.md, docs/dev/, README.md, tests/docs/, +CHANGELOG]
prev: [release/cli-migrate, release/cli-gaps, release/size-factors, release/formula-rename, release/augment]
---

# Update the docs for the 1.0 CLI

## Implementation plan

- [ ] @developer Regenerate the usage blocks from `--help`, add the docs usage test, state the help promise, document exit codes and completion, rewrite what describes the docstring-as-interface pattern, add the how-to-add-a-command note, CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR and build the docs <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B); widened
2026-11-19 for DETK-0025 Option B and the CLI gaps. Comes after every
node that changes the CLI (release/augment included, which adds a command), so the pages are written once.
`docs/formulas.md` belongs to release/formula-migrate and
release/formula-rename.
