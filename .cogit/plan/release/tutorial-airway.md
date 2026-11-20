---
kind: task
objective: 'The airway worked example becomes an executed tutorial: one page that is both the walkthrough and the test of the full DESeq2 workflow, ending in the published report and crate (DETK-0064)'
acceptance:
  - 'docs/tutorials/airway.md runs under the tutorial harness in the R job: data from the airway package, detk-stats summary, detk-filter, detk-norm deseq2 with --size-factors, detk-transform vst, detk-outlier entropy, detk-de deseq2 with the cell + dex design, detk-util annotate with gene symbols, the report and the crate'
  - 'the page shows checked outputs (the filtered gene count, the size factors, the top results with their symbols), and a test_airway.py checks the DESeq2 results against DESeq2 run directly in R on the same data'
  - 'the commands exist once: docs/example.md links the tutorial instead of repeating it, examples/airway/run.sh is removed or reduced to running the page and publishing the report, and tests/example/ no longer runs a copy'
  - 'the published example report and crate under docs/example/ are regenerated from the tutorial''s run; mkdocs build --strict passes; CHANGELOG'
from: [DETK-0064]
scope: [new:docs/tutorials/, docs/example.md, docs/example/, examples/airway/, tests/example/, new:tests/tutorials/, +mkdocs.yml, +CHANGELOG]
prev: [DETK-0064, release/tutorial-harness, release/cli-gaps, release/size-factors, release/formula-rename, release/r-design-names]
---

# Tutorial: differential expression on airway

## Implementation plan

- [ ] @developer Turn the airway example into the tutorial page with checked outputs and the DESeq2 comparison, retire the copies in run.sh and tests/example, regenerate the published report and crate; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Follow the page as a new user would, check its outputs against the report, and confirm the R job ran it <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 (DETK-0064, tutorial 1). Replaces the walkthrough and the
command copy that release/example made (#16, #33), so there is one source.
The fgsea step stays out of the test (it needs the network), as in the
current test; the page may show it as an optional step that is not run.
New files go under `docs/tutorials/`.
