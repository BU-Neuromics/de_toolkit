---
kind: step
time: 2026-11-25T19:42:33Z
by: DETK/reviewer
node: release/cut
step: s9
branch: node/168-cut
verdict: approve
commits: []
decisions: []
---

# Approved: Review the s5 change: the README's DOI badge shows and links the concept DOI Zenodo minted for v1.0.0 (10.5281/zenodo.24539251, resolving to the latest version), the PyPI badge reads 1.0.0, and the node's acceptance holds (PyPI 1.0.0 by release.yml, the Release with sdist and wheel, the DOI)

## Summary

Approved on head 4273e28. README: the DOI badge (zenodo.org/badge/DOI/10.5281/zenodo.24539251.svg) returns image/svg+xml showing 10.5281/zenodo.24539251, sits on its own line after the PyPI badge like the others; doi.org/10.5281/zenodo.24539251 resolves to zenodo.org/records/24539252, and the Zenodo API confirms 24539251 is the conceptdoi of record 24539252 (DOI 10.5281/zenodo.24539252, version v1.0.0, published 2026-11-25, isSupplementTo the v1.0.0 tree). The shields PyPI badge reads v1.0.0. Acceptance: PyPI serves 1.0.0 (wheel and sdist, uploaded 2026-11-25T18:51Z), and the provenance attestation names publisher GitHub BU-Neuromics/de_toolkit, workflow release.yml, environment pypi; release.yml run 45664275247 (attempt 2, push of v1.0.0 at 66628a8) succeeded in all three jobs. GitHub Release v1.0.0 is published, not draft or prerelease, and carries the wheel and sdist, whose sha256 match PyPI's. Tag v1.0.0 is annotated and points at 66628a8, the merge of #169. CITATION.cff (4273e28, added at the driver's request; outside the node's listed scope): version 1.0.0, date-released 2026-11-25, doi set to the concept DOI, identifiers with the concept and version DOIs, both checked against Zenodo; cffconvert --validate passes (schema 1.2.0). The diff holds only README.md, CITATION.cff and the .cogit plan and journal files. CI on 4273e28: all 12 checks pass, including test with R (bioconda).

## Artifacts

## Findings

## Questions
