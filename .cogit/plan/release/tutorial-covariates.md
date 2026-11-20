---
kind: task
objective: 'A tutorial derives covariates with the Miller recipes, records each step with detk-util record, fits a design that uses them, and shows the recorded steps in the crate (DETK-0050, DETK-0051, DETK-0064)'
acceptance:
  - 'docs/tutorials/covariates.md runs under the tutorial harness in the R job with mlr: from the airway data, a constant column, the z-score and the log of avgLength with the recipes of release/miller-recipes, each through detk-util record, one recipe failing on a deliberately bad value, then detk-de deseq2 with the z-scored column in the design'
  - 'the page shows checked outputs: the new columns, the failure''s message naming the sample, and the crate entries showing mlr (with its version) as the producer of the column data detk-de read'
  - 'it explains why formulas take column names only (DETK-0050) and links the recipes page and docs/formulas.md'
  - 'it is in the tutorials index and nav; mkdocs build --strict passes; CHANGELOG'
from: [DETK-0050, DETK-0051, DETK-0064]
scope: [new:docs/tutorials/, new:tests/tutorials/, +mkdocs.yml, +CHANGELOG]
prev: [DETK-0064, release/tutorial-airway, release/miller-recipes, release/record]
---

# Tutorial: derived covariates and recorded steps

## Implementation plan

- [ ] @developer Write the page with its checked outputs and crate check, index and nav; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Follow the page as a new user would and check the crate entries <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 (DETK-0064, tutorial 3). After release/tutorial-airway,
whose data step it reuses (keeping avgLength in the sample sheet). New pages
go under `docs/tutorials/`.
