---
kind: task
objective: 'detk-norm deseq2 --size-factors=FILE writes the size factors it computes, as its help says (DETK-0029 Option A; tracks #44)'
acceptance:
  - '--size-factors=FILE writes a two-column tab-separated file, sample name and size factor, one row per sample in the counts file''s column order, with sample names kept as written (zero-padded IDs stay padded, DETK-0015); a test checks the file against the size factors the module computes, and that the counts output is unchanged'
  - 'without the option nothing extra is written; the values in the file are the ones already recorded in the module JSON''s properties.size_factors, which stay as they are'
  - 'the cli-pin table changes from "accepted, writes nothing" to "writes the file"; examples/airway/run.sh, docs/example.md and the skill''s commands.md keep their usage and now describe a file that is written'
  - 'the CHANGELOG says what changed'
from: [DETK-0029]
scope: [de_toolkit/norm.py, docs/example.md, examples/airway/run.sh, tests/norm/, tests/cli/, skills/detk/references/commands.md, +CHANGELOG]
prev: [DETK-0029, release/cli-migrate, DETK-0082]
issue: 86
visited: 92d4fab
status: done
done: 4669f6f
---

# --size-factors writes the size factors

## Implementation plan

- [x] @developer Write the size factors file from `self.size_factors` with tests, update the cli-pin row, check the example and the skill describe it; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's word, from the reviews of de_toolkit#40, #41 and #42.
Moved from `features` into `release` on 2026-11-19: Adam put all the CLI
gaps in 1.0 (DETK-0025). Comes after release/cli-migrate, which rewrites
`norm.py`'s command line. Adam chose to implement it (DETK-0029,
"implement it", 2026-11-19).
