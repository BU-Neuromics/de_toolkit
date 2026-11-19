---
kind: task
objective: 'detk-norm deseq2 --size-factors=FILE writes the size factors, or the option is removed, per DETK-0029, and the worked example matches (tracks #44)'
acceptance:
  - 'under DETK-0029 Option A, --size-factors=FILE writes a two-column tab-separated file of sample name and size factor, as help says, with a test; under Option B the option is gone and the example no longer uses it'
  - 'examples/airway/run.sh, docs/example.md and the skill''s references agree with the choice, and the cli-pin table is updated'
  - 'the CHANGELOG says what changed'
from: [DETK-0029]
scope: [de_toolkit/norm.py, docs/example.md, examples/airway/run.sh, tests/norm/, tests/cli/, skills/detk/references/commands.md, +CHANGELOG]
prev: [DETK-0029, release/cli-migrate]
---

# --size-factors writes or goes

## Implementation plan

- [ ] @developer Carry out DETK-0029 with tests, the example and a CHANGELOG entry; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.
Moved from `features` into `release` on 2026-11-19: Adam put all the CLI
gaps in 1.0 (DETK-0025). Comes after release/cli-migrate, which rewrites
`norm.py`'s command line. Whether to implement or remove is DETK-0029.
