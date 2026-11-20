---
kind: task
objective: 'A tutorial takes salmon outputs to a normalized matrix and a report with no R: gather, tidy, CPM and TPM, plog, summary statistics, report and crate; it runs in every test job (DETK-0064)'
acceptance:
  - 'docs/tutorials/quantifiers.md runs under the tutorial harness in every test job (no R): detk-util gather on salmon quant.sf files, detk-util tidy against a sample sheet, detk-norm cpm and tpm, detk-transform plog, detk-stats summary, and the report and crate'
  - 'its data are small committed files simulated by a committed, seeded script (a few samples, a few hundred transcripts), so there is no licence question, and the script reproduces them byte for byte'
  - 'the page shows checked outputs: the gathered matrix''s first lines with IDs as written, a sample''s CPM summing to one million, and the steps listed in the crate; a test_quantifiers.py checks the TPM against a direct computation'
  - 'it is in the tutorials index and nav; mkdocs build --strict passes; CHANGELOG'
from: [DETK-0064]
scope: [new:docs/tutorials/, new:tests/tutorials/, +mkdocs.yml, +CHANGELOG]
prev: [DETK-0064, release/tutorial-harness, release/cli-gaps]
issue: 100
visited: f3a014f
---

# Tutorial: from quantifier outputs to a normalized matrix

## Implementation plan

- [x] @developer Write the data script and data, the page with its checked outputs and the TPM check, index and nav; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Follow the page as a new user would, run it locally, and check its outputs and the data script <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 (DETK-0064, tutorial 2). The one tutorial with no R, so it
runs on every Python in CI. Written on the final CLI (after release/cli-gaps).
