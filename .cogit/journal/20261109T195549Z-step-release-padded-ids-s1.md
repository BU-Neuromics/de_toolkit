---
kind: step
time: 2026-11-09T19:55:49Z
by: DETK/developer
node: release/padded-ids
step: s1
branch: node/48-padded-ids
verdict: done
commits: [b6e455e, 686b086]
decisions: [DETK-0015]
---

# Done: Fix it with tests and a CHANGELOG entry; open the PR

## Summary

The shared reader (common.read_id_table, used by CountMatrixFile for counts and sample info) reads the ID column as text exactly as written, counts and covariates keep pandas' types; 007 survives and matches a lengths file. Tests in tests/common: header variants, stream/gzip, versioned and Entrez IDs, padded sample names, tpm/fpkm against a lengths file, and 11 CLI commands writing 007 back (14 of them fail on the old reader). norm.md and the CHANGELOG updated. The R-backed commands (de deseq2/firth, transform vst/rlog) still re-type 007 as 7 in R and in wrapr's read-back, unchanged from before: outside the scope and untestable without R, asked as DETK-0015. Done because the shared reader, its tests and docs are complete; the R boundary is Adam's call.

## Artifacts

## Findings

## Questions

- DETK-0015 Zero-padded IDs through the R-backed commands

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
