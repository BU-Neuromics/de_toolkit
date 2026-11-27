---
kind: step
time: 2026-11-27T19:31:08Z
by: DETK/reviewer
node: release-1-0-1/quickstart-deseq2
step: s2
branch: review/quickstart-deseq2
verdict: approve
commits: [df37c33]
decisions: [DETK-0770]
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: reproduction fails on v1.0.0 (2 of 3) and passes here; acceptance holds; scope clean; CI green incl. R

## Artifacts

## Findings

- Reproduction: tests/docs/test_quickstart_deseq2.py run against v1.0.0's docs/ fails test_quickstart_names_how_deseq2_differs and test_quickstart_links_de_page_by_the_example; test_de_page_states_the_matched_settings passes there (a precondition on de.md, as the acceptance describes). All 34 tests/docs tests pass on 0ca7498 (uv run pytest tests/docs).
- Acceptance: the paragraph directly after the bash example names independent filtering and Cook's distance and links tools/de.md#deseq2 (strict docs build passes, so the anchor resolves). Its claims match de_toolkit/de.py: nbinomWaldTest, p.adjust(method='fdr') = BH per coefficient, every coefficient by default (--last-term-only off), no results() call, so no independent filtering or Cook's cutoff.
- Scope: changes are docs/quickstart.md, tests/docs/test_quickstart_deseq2.py, CHANGELOG (new 1.0.1 section, Fixed) and the node's .cogit records. Nothing else.
- CI on #188: all checks pass, including 'test with R (bioconda)' (27m) and 'docs build (strict)'.
- Non-blocking, outside scope: docs/tools/de.md's 'roughly equivalent' R block calls results(dds, cooksCutoff=Inf), which leaves independentFiltering=TRUE, so it is not the matched setting the new quickstart text sends readers there for. Recorded as DETK-0770 (Proposed; recommends a follow-up node in release-1-0-1).
- Nit: 'BH adjustment over all genes' is strictly over genes with a p-value (p.adjust drops NA, e.g. all-zero rows); the quickstart example filters those first, so no change asked.

## Questions

- DETK-0770 docs/tools/de.md's DESeq2 R equivalent omits independentFiltering=FALSE (#197)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
