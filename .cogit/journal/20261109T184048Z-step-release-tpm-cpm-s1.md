---
kind: step
time: 2026-11-09T18:40:48Z
by: DETK/developer
node: release/tpm-cpm
step: s1
branch: node/24-tpm-cpm
verdict: done
commits: [d55f89d, b0c692d, d572b80]
decisions: [DETK-0005]
---

# Done: Implement with tests, a report view, the docs page and a CHANGELOG entry; open the PR

## Summary

detk-norm cpm and tpm with report views, tests, docs and CHANGELOG (PR #40), plus the library/fpkm CLI fixes. Fixes for the s2 review: (1) feature IDs matched as text on both sides, so numeric/Entrez IDs work for tpm and fpkm, output index unchanged; (2) a feature listed twice in the lengths file (or Series) raises NormalizationException; (3) the first line is a header only when its length field is text that is not a number or a missing-value token (NA, NaN, N/A, NULL, None, empty), so a first length of NA reports 'not a positive number'; (4) tests for the all-zero sample (NaN plus warning) for cpm and tpm; (5) lengths-file rules in CHANGELOG, docs/tools/norm.md and the CLI help; DETK-0005 revised to record them. FPKM arithmetic unchanged, per DETK-0006 (Accepted). pytest 178 passed, 49 skipped; ruff check/format and mkdocs --strict clean. Commits d55f89d, b0c692d, d572b80.

## Artifacts

## Findings

## Questions
