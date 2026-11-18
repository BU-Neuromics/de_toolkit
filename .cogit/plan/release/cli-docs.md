---
kind: task
objective: 'The docs show the migrated CLI as it is and say how commands are now defined, kept in step by a test (DETK-0001)'
acceptance:
  - 'every usage block in docs/tools/*.md and docs/report.md matches the installed --help, and a test in CI checks it as DETK-0010''s test does for the skill'
  - 'docs/index.md and docs/api.md (where the #37 statement says the CLI is the promise) state what help promises, as DETK-0025 sets it'
  - 'no page describes command lines as built from docopt docstrings; the developer docs say how to add a command or option with the DETK-0023 parser'
  - 'the README, quickstart and example commands run as written on the migrated CLI'
  - 'uv run --group docs mkdocs build --strict passes'
from: [DETK-0001, DETK-0025]
scope: [docs/tools/, docs/report.md, docs/index.md, docs/quickstart.md, docs/concepts.md, docs/api.md, docs/agent-skills.md, docs/example.md, docs/dev/, README.md, tests/docs/, +CHANGELOG]
prev: [release/cli-migrate, release/formula-migrate]
---

# Update the docs for the migrated CLI

## Implementation plan

- [ ] @developer Regenerate the usage blocks from `--help`, add the docs usage test, rewrite what describes the docstring-as-interface pattern, add the how-to-add-a-command note, CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR and build the docs <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B). After both
migrations so the pages are written once. `docs/formulas.md` is updated
by release/formula-migrate.
