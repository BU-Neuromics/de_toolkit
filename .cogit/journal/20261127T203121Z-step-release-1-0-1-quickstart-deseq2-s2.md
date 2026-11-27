---
kind: step
time: 2026-11-27T20:31:21Z
by: DETK/reviewer
node: release-1-0-1/quickstart-deseq2
step: s2
branch: review/quickstart-deseq2
verdict: approve
commits: [095e424, 5eafd7a, 7995659]
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved again after DETK-0770's fix: de.md's R block now turns off both settings, pinned by a test; scope and CI clean

## Artifacts

## Findings

- DETK-0770 is Accepted (option 1: widen this node to docs/tools/de.md). 095e424 changes de.md's R equivalent to results(dds, independentFiltering=FALSE, cooksCutoff=Inf). That now matches de_toolkit/de.py (nbinomWaldTest, then BH per coefficient, with no independent filtering or Cook's cutoff) and the page's own prose.
- The new test_de_page_r_block_turns_off_both fails on de.md as it was before 095e424 and passes after it. The full tests/docs suite passes at 7995659 (34 passed, 1 skipped: an R-gated test, since this machine has no R).
- The CHANGELOG 1.0.1 entry now names the de.md change and DETK-0770.
- Scope: 5eafd7a records docs/tools/de.md as an edited file in scope, which is right for a one-line change. Against main, the node changes only CHANGELOG, docs/quickstart.md, docs/tools/de.md and tests/docs/test_quickstart_deseq2.py. 7995659 is a clean merge of main and adds nothing of the node's.
- CI on 7995659: every check passes, including 'test with R (bioconda)' and 'docs build (strict)'.
- Nit, no change asked: DETK-0770's Decision section still recommends option 2. The revision line records that option 1 was accepted.

## Questions
